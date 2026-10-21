"""Programmatic Babylon operations, shared by the CLI and (later) the API.

Three problems of the historical CLI code are handled here:

1. Global state: deployers read context/tenant/variable files from the process-wide
   `Environment` singleton. `_bound_environment` fills it for the duration of one
   operation, restores it afterwards, and refuses a second concurrent operation.
2. `sys.exit()`: several helpers call it on fatal errors. It is caught per manifest
   and turned into a FAILED outcome instead of killing the process.
3. Ignored failures: every manifest gets a ResourceOutcome, so the caller knows
   exactly what succeeded and what failed.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from logging import getLogger
from pathlib import Path
from typing import Any

from Babylon.core.errors import OperationInProgressError
from Babylon.core.manifests import Manifest, load_manifests, plan_apply
from Babylon.core.models import ApplyOptions, ApplyResult, ResourceOutcome, ResourceStatus
from Babylon.core.selection import resolve_resources
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)

# A deployer deploys one manifest. Returning CommandResponse.fail() (or raising) means failure.
Deployer = Callable[[Manifest, Path], Any]

_operation_lock = threading.Lock()


@contextmanager
def _bound_environment(context: str, tenant: str, variable_files: tuple[Path, ...]) -> Iterator[Environment]:
    """Bind the Environment singleton to one operation, then restore it."""
    if not _operation_lock.acquire(blocking=False):
        raise OperationInProgressError("A Babylon operation is already running in this process")
    env = Environment()
    saved = (env.context_id, env.environ_id, list(env.variable_files), env.remote)
    try:
        # `remote` is only ever switched on (by a manifest or the local state), never off:
        # start each operation from the default so it cannot leak from a previous one.
        env.remote = False
        env.set_context(context)
        env.set_environ(tenant)
        env.set_variable_files([Path(f) for f in variable_files])
        yield env
    finally:
        env.context_id, env.environ_id, env.variable_files, env.remote = saved
        _operation_lock.release()


def default_deployers() -> dict[str, Deployer]:
    """The real Babylon deployers (imported lazily: they pull heavy SDKs)."""
    from Babylon.commands.macro.build import build
    from Babylon.commands.macro.deploy_organization import deploy_organization
    from Babylon.commands.macro.deploy_solution import deploy_solution
    from Babylon.commands.macro.deploy_webapp import deploy_webapp
    from Babylon.commands.macro.deploy_workspace import deploy_workspace

    return {
        "build": lambda m, d: build(namespace=m.namespace, file_content=m.content),
        "organization": lambda m, d: deploy_organization(namespace=m.namespace, file_content=m.content),
        "solution": lambda m, d: deploy_solution(namespace=m.namespace, file_content=m.content),
        "webapp": lambda m, d: deploy_webapp(namespace=m.namespace, file_content=m.content),
        "workspace": lambda m, d: deploy_workspace(namespace=m.namespace, file_content=m.content, deploy_dir=d),
    }


def _run_one(deployer: Deployer, manifest: Manifest, deploy_dir: Path) -> str | None:
    """Deploy one manifest. Returns an error message, or None on success."""
    try:
        ret = deployer(manifest, deploy_dir)
    except SystemExit as exc:
        return f"aborted by a fatal error (exit code {exc.code}), see logs"
    except Exception as exc:  # noqa: BLE001 - any SDK/API error becomes a failed resource
        logger.exception(f"  [bold red]✘[/bold red] {manifest.path.name}: {exc}")
        return f"{type(exc).__name__}: {exc}"
    if isinstance(ret, CommandResponse) and ret.has_failed():
        return "deployment reported a failure, see logs"
    return None


def apply(options: ApplyOptions, deployers: Mapping[str, Deployer] | None = None) -> ApplyResult:
    """Deploy the manifests of `options.deploy_dir` (equivalent of `babylon apply`).

    With `options.fail_fast` (default), the first failure stops the run and the
    remaining manifests are reported as SKIPPED.

    Args:
        options: explicit inputs.
        deployers: optional replacement of the real deployers (used by tests).

    Raises:
        InvalidOptionsError: bad include/exclude, missing directory, unreadable manifest
            (raised before anything is deployed).
        OperationInProgressError: another operation is running in this process.
    """
    # 1. Validate and plan: no side effect yet.
    selected = resolve_resources(options.include, options.exclude)
    plan = plan_apply(load_manifests(options.deploy_dir), selected)
    deployers = deployers if deployers is not None else default_deployers()

    # 2. Execute, one outcome per manifest.
    result = ApplyResult(context=options.context, tenant=options.tenant)
    with _bound_environment(options.context, options.tenant, options.variable_files):
        for manifest in plan:
            if options.fail_fast and not result.succeeded:
                result.resources.append(
                    ResourceOutcome(manifest.resource, manifest.path.name, ResourceStatus.SKIPPED, "previous resource failed")
                )
                continue
            error = _run_one(deployers[manifest.resource], manifest, Path(options.deploy_dir))
            status = ResourceStatus.FAILED if error else ResourceStatus.SUCCEEDED
            result.resources.append(ResourceOutcome(manifest.resource, manifest.path.name, status, error))
    return result
