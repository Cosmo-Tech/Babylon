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

from Babylon.core.destroy import DestroyTarget, is_full_destroy, plan_destroy, resource_id
from Babylon.core.errors import OperationInProgressError
from Babylon.core.manifests import Manifest, load_manifests, plan_apply
from Babylon.core.models import (
    ApplyOptions,
    ApplyResult,
    DestroyOptions,
    DestroyOutcome,
    DestroyResult,
    ResourceOutcome,
    ResourceStatus,
)
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


def _guarded(call: Callable[[], Any], name: str) -> tuple[Any, str | None]:
    """Run `call`; turn sys.exit() and exceptions into an error message instead of crashing."""
    try:
        return call(), None
    except SystemExit as exc:
        return None, f"aborted by a fatal error (exit code {exc.code}), see logs"
    except Exception as exc:  # noqa: BLE001 - any SDK/API error becomes a failed resource
        logger.exception(f"  [bold red]✘[/bold red] {name}: {exc}")
        return None, f"{type(exc).__name__}: {exc}"


def _run_one(deployer: Deployer, manifest: Manifest, deploy_dir: Path) -> str | None:
    """Deploy one manifest. Returns an error message, or None on success."""
    ret, error = _guarded(lambda: deployer(manifest, deploy_dir), manifest.path.name)
    if error:
        return error
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


# destroy

# A deleter deletes one resource and clears its id from the state it receives.
Deleter = Callable[[dict], Any]

# Receives the plan, returns True to go on. None means "already confirmed" (API).
Confirm = Callable[[list[DestroyTarget]], bool]


def default_deleters() -> dict[str, Deleter]:
    """The real Babylon deleters (imported lazily). Credentials are fetched once, on first use."""
    from Babylon.commands.api.organization import get_organization_api_instance
    from Babylon.commands.api.solution import get_solution_api_instance
    from Babylon.commands.macro.destroy import _destroy_workspace_resources
    from Babylon.commands.macro.helpers.webapp import destroy_webapp
    from Babylon.commands.macro.helpers.workspace import delete_api_resource
    from Babylon.utils.credentials import get_keycloak_token

    creds: dict = {}

    def credentials() -> tuple[str, dict]:
        if not creds:
            creds["token"], creds["config"] = get_keycloak_token()
        return creds["token"], creds["config"]

    def org_id(state: dict) -> str:
        return state["services"]["api"]["organization_id"]

    def delete_solution(state: dict) -> None:
        token, config = credentials()
        api = get_solution_api_instance(config=config, keycloak_token=token)
        sol_id = state["services"]["api"]["solution_id"]
        delete_api_resource(api.delete_solution, "Solution", org_id(state), sol_id, state, "solution_id")

    def delete_workspace(state: dict) -> None:
        token, config = credentials()
        _destroy_workspace_resources(state, config, token, org_id(state))

    def delete_organization(state: dict) -> None:
        token, config = credentials()
        api = get_organization_api_instance(config=config, keycloak_token=token)
        delete_api_resource(api.delete_organization, "Organization", None, org_id(state), state, "organization_id")

    return {
        "solution": delete_solution,
        "workspace": delete_workspace,
        "organization": delete_organization,
        "webapp": destroy_webapp,
    }


def _save_state(env: Environment, state: dict) -> None:
    """Persist the state after destroy: removed when everything is gone, updated otherwise.

    Same behaviour as the historical CLI (local file + Kubernetes secret when remote).
    """
    remote = bool(state.get("remote"))
    if is_full_destroy(state):
        logger.info("  [dim]🗑 All resources cleared ! removing state...[/dim]")
        if not env.delete_state_in_local():
            logger.warning("  [yellow]⚠[/yellow] Could not delete the local state file, it may need manual cleanup.")
        if remote and not env.delete_state_in_kubernetes():
            logger.warning("  [yellow]⚠[/yellow] Could not delete the remote state secret, it may need manual cleanup.")
    else:
        logger.info("  [dim]↻ Partial destroy ! persisting updated state...[/dim]")
        env.store_state_in_local(state=state)
        if remote:
            env.store_state_in_kubernetes(state=state)


def destroy(
    options: DestroyOptions,
    confirm: Confirm | None = None,
    deleters: Mapping[str, Deleter] | None = None,
) -> DestroyResult:
    """Destroy the resources recorded in the state (equivalent of `babylon destroy`).

    Steps: load state -> plan (validation) -> confirm -> delete in DESTROY_ORDER -> save state.

    Args:
        options: explicit inputs.
        confirm: called with the plan before deleting anything; returning False cancels.
            None = no question asked (the API confirms in the request itself).
        deleters: optional replacement of the real deleters (used by tests).

    Raises:
        InvalidOptionsError: bad include/exclude, or a parent would be destroyed while a
            deployed child is kept (raised before the confirmation, nothing is deleted).
        OperationInProgressError: another operation is running in this process.
    """
    selected = resolve_resources(options.include, options.exclude)
    result = DestroyResult(context=options.context, tenant=options.tenant)

    with _bound_environment(options.context, options.tenant, options.variable_files) as env:
        # 1. Read the state and plan: no side effect yet.
        state = env.retrieve_state_func()
        plan = plan_destroy(state, selected)
        result.state = state

        # 2. Ask before deleting.
        if confirm is not None and not confirm(plan):
            result.cancelled = True
            return result

        # 3. Delete, one outcome per resource.
        deleters = deleters if deleters is not None else default_deleters()
        for target in plan:
            if not target.deployed:
                outcome = DestroyOutcome(target.resource, None, ResourceStatus.SKIPPED, "not deployed")
            elif options.fail_fast and not result.succeeded:
                outcome = DestroyOutcome(target.resource, target.resource_id, ResourceStatus.SKIPPED, "previous resource failed")
            else:
                _, error = _guarded(lambda t=target: deleters[t.resource](state), target.label)
                if not error and resource_id(state, target.resource):
                    error = "still present in state after deletion, see logs"
                status = ResourceStatus.FAILED if error else ResourceStatus.SUCCEEDED
                outcome = DestroyOutcome(target.resource, target.resource_id, status, error)
            result.resources.append(outcome)

        # 4. Persist what really happened (also after a failure: deleted ids must not come back).
        _save_state(env, state)
    return result
