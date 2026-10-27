"""Entry point of the Kubernetes Job created by the API: `python -m babylon_api.worker`.

One Job = one operation = one process. This is why the `Environment` singleton is not a
problem here: nobody else runs in this process.

Input:  env BABYLON_OPERATION = {"operation": "apply" | "destroy", "request": {...}}
        (the validated API request, as JSON; no secret inside: secrets come from env/envFrom).
Output: a short JSON summary written to the container termination message
        (/dev/termination-log, read back by the API), and exit code 0 (success) / 1 (failure).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager, nullcontext
from pathlib import Path

from Babylon.core.errors import BabylonError
from Babylon.core.models import ApplyOptions, DestroyOptions
from Babylon.core.operations import Deleter, Deployer
from Babylon.core.operations import apply as core_apply
from Babylon.core.operations import destroy as core_destroy
from Babylon.utils.environment import Environment
from babylon_api.repository import prepare_checkout
from babylon_api.schemas import ApplyRequest, DestroyRequest

logger = logging.getLogger("babylon_api.worker")

OPERATION_ENV = "BABYLON_OPERATION"
OPERATION_ID_ENV = "BABYLON_OPERATION_ID"  # lock holder identity
LOCK_NAMESPACE_ENV = "BABYLON_LOCK_NAMESPACE"  # where the Leases live (the API namespace)
LOCK_DURATION_ENV = "BABYLON_LOCK_DURATION"  # seconds, > Job deadline
RESULT_PATH_ENV = "BABYLON_RESULT_PATH"

# (context, tenant) -> context manager holding the lock
LockFactory = Callable[[str, str], AbstractContextManager]
DEFAULT_RESULT_PATH = "/dev/termination-log"
MAX_RESULT_BYTES = 4096  # Kubernetes truncates termination messages above 4 KiB
MAX_ERROR_CHARS = 300


def _short(message: str | None) -> str | None:
    if message is None or len(message) <= MAX_ERROR_CHARS:
        return message
    return message[: MAX_ERROR_CHARS - 3] + "..."


def run(
    payload: dict,
    workdir: Path,
    environ: Mapping[str, str] | None = None,
    deployers: Mapping[str, Deployer] | None = None,
    deleters: Mapping[str, Deleter] | None = None,
    lock: LockFactory | None = None,
) -> dict:
    """Validate the payload again, take the tenant lock, fetch the repository, run the operation.

    Raises BabylonError / ValueError (pydantic) for a bad payload or repository,
    OperationInProgressError when another operation holds the tenant lock.
    """
    operation = payload.get("operation")
    schema = {"apply": ApplyRequest, "destroy": DestroyRequest}.get(operation)
    if schema is None:
        raise ValueError(f"unknown operation {operation!r}")
    # Defense in depth: the Job env could have been edited; never trust it more than an HTTP body.
    request = schema.model_validate(payload.get("request"))

    # The lock is taken before anything else (validation excepted) and released even on error.
    with lock(request.context, request.tenant) if lock else nullcontext():
        return _execute(operation, request, workdir, environ, deployers, deleters)


def _execute(operation, request, workdir, environ, deployers, deleters) -> dict:
    checkout = prepare_checkout(
        url=str(request.repository.url),
        ref=request.repository.ref,
        dest=workdir / "repo",
        deploy_dir=getattr(request, "deploy_dir", None),
        variable_files=request.variable_files,
        environ=environ,
    )
    # The local state is a throw-away copy (the pod disk is lost); the real state is the Kubernetes Secret.
    Environment().state_dir = workdir / "state"

    common = dict(
        context=request.context,
        tenant=request.tenant,
        variable_files=checkout.variable_files,
        include=tuple(request.include),
        exclude=tuple(request.exclude),
        fail_fast=True,
        force_remote=True,
    )
    if operation == "apply":
        result = core_apply(ApplyOptions(deploy_dir=checkout.deploy_dir, **common), deployers=deployers)
        resources = [{"resource": r.resource, "file": r.file, "status": r.status, "error": _short(r.error)} for r in result.resources]
    else:
        # confirm=None: the confirmation is `confirm: true` in the HTTP request, already validated.
        result = core_destroy(DestroyOptions(**common), confirm=None, deleters=deleters)
        resources = [
            {"resource": r.resource, "id": r.resource_id, "status": r.status, "error": _short(r.error)} for r in result.resources
        ]
    return {
        "status": "succeeded" if result.succeeded else "failed",
        "operation": operation,
        "commit": checkout.commit,
        "resources": resources,
    }


def fit(summary: dict) -> str:
    """JSON of the summary, guaranteed to fit in a termination message."""
    text = json.dumps(summary, default=str)
    if len(text.encode()) <= MAX_RESULT_BYTES:
        return text
    reduced = {k: v for k, v in summary.items() if k != "resources"}
    reduced["error"] = _short(reduced.get("error")) or "result too large, see the Job logs"
    return json.dumps(reduced, default=str)[:MAX_RESULT_BYTES]


def write_result(text: str, environ: Mapping[str, str] | None = None) -> None:
    environ = os.environ if environ is None else environ
    try:
        Path(environ.get(RESULT_PATH_ENV, DEFAULT_RESULT_PATH)).write_text(text)
    except OSError:
        logger.warning("could not write the termination message (not running in Kubernetes?)")


def lock_from_env(environ: Mapping[str, str]) -> LockFactory | None:
    """The Lease lock configured by the Job (build_job). None outside a Job (local runs, tests)."""
    namespace, holder = environ.get(LOCK_NAMESPACE_ENV), environ.get(OPERATION_ID_ENV)
    if not namespace or not holder:
        return None
    duration = int(environ.get(LOCK_DURATION_ENV) or 3900)

    def factory(context: str, tenant: str) -> AbstractContextManager:
        from kubernetes import client

        from Babylon.core.kube import load_kubernetes_config
        from babylon_api.lock import tenant_lock

        load_kubernetes_config(environ=environ)
        return tenant_lock(client.CoordinationV1Api(), namespace, context, tenant, holder, duration)

    return factory


def main(environ: Mapping[str, str] | None = None) -> int:
    environ = os.environ if environ is None else environ
    try:
        payload = json.loads(environ[OPERATION_ENV])
        with tempfile.TemporaryDirectory(prefix="babylon-") as tmp:
            summary = run(payload, Path(tmp), environ=environ, lock=lock_from_env(environ))
    except KeyError:
        summary = {"status": "failed", "error": f"{OPERATION_ENV} is not set"}
    except (BabylonError, ValueError) as exc:  # bad payload, host refused, git failure, invalid paths...
        summary = {"status": "failed", "error": _short(f"{type(exc).__name__}: {exc}")}
    except Exception as exc:  # noqa: BLE001 - report anything, the Job must end with a readable result
        logger.exception("unexpected error")
        summary = {"status": "failed", "error": _short(f"{type(exc).__name__}: {exc}")}

    text = fit(summary)
    write_result(text, environ)
    print(text)  # also in `kubectl logs`
    return 0 if summary["status"] == "succeeded" else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    sys.exit(main())
