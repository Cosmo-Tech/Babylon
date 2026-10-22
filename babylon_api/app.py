"""FastAPI application. health check + request validation only.

Run locally:  uvicorn babylon_api.app:app --reload
Docs:         http://127.0.0.1:8000/docs  (generated from the pydantic schemas)
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from Babylon.core.errors import InvalidOptionsError, OperationInProgressError
from Babylon.version import VERSION
from babylon_api.schemas import ApplyRequest, DestroyRequest, ValidatedResponse

app = FastAPI(
    title="Babylon API",
    version=VERSION,
    description="Run `babylon apply` / `babylon destroy` through HTTP.",
)


# Core errors -> HTTP status codes (the core never knows about HTTP, like it never knows about click).
@app.exception_handler(InvalidOptionsError)
async def _invalid_options(_: Request, exc: InvalidOptionsError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(exc)})


@app.exception_handler(OperationInProgressError)
async def _in_progress(_: Request, exc: OperationInProgressError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.get("/healthz", tags=["health"])
def healthz() -> dict:
    """Liveness probe for Kubernetes: the process answers. Checks nothing else on purpose."""
    return {"status": "ok"}


@app.post("/apply", tags=["operations"], response_model=ValidatedResponse)
def apply(request: ApplyRequest) -> ValidatedResponse:
    """Validate an apply request. FastAPI already returned 422 if the body was invalid."""
    return ValidatedResponse(operation="apply", request=request)


@app.post("/destroy", tags=["operations"], response_model=ValidatedResponse)
def destroy(request: DestroyRequest) -> ValidatedResponse:
    """Validate a destroy request (`confirm: true` is mandatory)."""
    return ValidatedResponse(operation="destroy", request=request)
