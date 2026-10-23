"""FastAPI application: validates requests and runs each operation as a Kubernetes Job.

Run locally:  uvicorn babylon_api.app:app --reload
Docs:         http://127.0.0.1:8000/docs  (generated from the pydantic schemas)

Flow:  POST /apply -> 202 {operation_id}  ->  Job babylon-apply-<id> runs the worker
       GET /operations/{operation_id}     ->  pending | running | succeeded | failed (+ result)
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Request, status
from fastapi.responses import JSONResponse
from kubernetes import client
from kubernetes.client.exceptions import ApiException

from Babylon.core.errors import InvalidOptionsError, KubernetesAuthError, OperationInProgressError
from Babylon.core.kube import load_kubernetes_config
from Babylon.version import VERSION
from babylon_api.jobs import ApiConfigurationError, JobSettings, build_job, get_operation, new_operation_id
from babylon_api.repository import allowed_hosts, check_allowed_host
from babylon_api.schemas import ApplyRequest, DestroyRequest, OperationAccepted, OperationStatus

app = FastAPI(
    title="Babylon API",
    version=VERSION,
    description="Run `babylon apply` / `babylon destroy` through HTTP, as Kubernetes Jobs.",
)


@dataclass(frozen=True)
class KubeClients:
    batch: client.BatchV1Api
    core: client.CoreV1Api


@lru_cache(maxsize=1)
def get_kube() -> KubeClients:
    """Kubernetes clients, created once (in-cluster ServiceAccount in the pod, kubeconfig locally)."""
    load_kubernetes_config()
    return KubeClients(batch=client.BatchV1Api(), core=client.CoreV1Api())


def get_settings() -> JobSettings:
    return JobSettings.from_env()


Kube = Annotated[KubeClients, Depends(get_kube)]
Settings = Annotated[JobSettings, Depends(get_settings)]


# errors -> HTTP status codes (the core never knows about HTTP) 

@app.exception_handler(InvalidOptionsError)
async def _invalid_options(_: Request, exc: InvalidOptionsError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(exc)})


@app.exception_handler(OperationInProgressError)
async def _in_progress(_: Request, exc: OperationInProgressError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.exception_handler(ApiConfigurationError)
@app.exception_handler(KubernetesAuthError)
async def _not_ready(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": str(exc)})


@app.exception_handler(ApiException)
async def _kubernetes_error(_: Request, exc: ApiException) -> JSONResponse:
    # e.g. 403 when the API ServiceAccount may not create Jobs: our dependency failed, not the client.
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": f"Kubernetes API error: {exc.status} {exc.reason}"},
    )

# routes

@app.get("/healthz", tags=["health"])
def healthz() -> dict:
    """Liveness probe for Kubernetes: the process answers. Checks nothing else on purpose."""
    return {"status": "ok"}


def _submit(operation: str, request: ApplyRequest | DestroyRequest, kube: KubeClients, settings: JobSettings):
    check_allowed_host(str(request.repository.url), allowed_hosts())  # refuse before creating anything
    operation_id = new_operation_id()
    job = build_job(operation, request, operation_id, settings)
    kube.batch.create_namespaced_job(namespace=settings.namespace, body=job)
    return OperationAccepted(operation_id=operation_id, operation=operation, job_name=job.metadata.name)


@app.post("/apply", tags=["operations"], status_code=status.HTTP_202_ACCEPTED, response_model=OperationAccepted)
def apply(request: ApplyRequest, kube: Kube, settings: Settings) -> OperationAccepted:
    """Start an apply. 202 = accepted, not finished: poll GET /operations/{operation_id}."""
    return _submit("apply", request, kube, settings)


@app.post("/destroy", tags=["operations"], status_code=status.HTTP_202_ACCEPTED, response_model=OperationAccepted)
def destroy(request: DestroyRequest, kube: Kube, settings: Settings) -> OperationAccepted:
    """Start a destroy (`confirm: true` is mandatory)."""
    return _submit("destroy", request, kube, settings)


@app.get("/operations/{operation_id}", tags=["operations"], response_model=OperationStatus)
def operation_status(operation_id: Annotated[str, Path(pattern=r"^[0-9a-f]{12}$")], kube: Kube, settings: Settings) -> OperationStatus:
    found = get_operation(kube.batch, kube.core, settings.namespace, operation_id)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown operation (or older than the Job TTL)")
    return OperationStatus(**found)
