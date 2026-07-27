"""
Cosmotech API helpers for workspace deployment and teardown.

Public surface:
  - create_workspace     — create a new workspace, persist its ID in state
  - update_workspace     — update an existing workspace + sync security
  - delete_api_resource  — generic idempotent deletion (org / solution / workspace)

Internal helper called by update_workspace:
  - sync_workspace_security
"""

from logging import getLogger
from typing import Callable

from cosmotech_api.models.workspace_create_request import WorkspaceCreateRequest
from cosmotech_api.models.workspace_security import WorkspaceSecurity
from cosmotech_api.models.workspace_update_request import WorkspaceUpdateRequest

from Babylon.commands.macro.helpers.common import update_object_security

from typing import Tuple

logger = getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _deploy_or_update_workspace(api_instance, api_section, payload, existing_workspace_id: str = "") -> tuple[bool, str]:
    """Create or update workspace via API.

    ``existing_workspace_id`` is the ID already stored in the workspaces block
    (empty string means *create new*).

    Returns ``(success, final_workspace_id)``.  The caller is responsible for
    persisting ``final_workspace_id`` in the correct state slot.
    """
    if not existing_workspace_id:
        new_id = create_workspace(api_instance, api_section, payload)
        if new_id is None:
            return False, ""
        return True, new_id
    ok = update_workspace(api_instance, api_section, payload, existing_workspace_id)
    return ok, existing_workspace_id if ok else ""


def create_workspace(api_instance, api_section: dict, payload: dict) -> str | None:
    """Create a new workspace via the API.

    Returns the new workspace ID on success, or ``None`` on failure.
    The caller is responsible for persisting the ID in the correct state slot.
    """
    logger.info("  [dim]→ No existing workspace ID found. Creating...[/dim]")
    workspace = api_instance.create_workspace(
        organization_id=api_section["organization_id"],
        workspace_create_request=WorkspaceCreateRequest.from_dict(payload),
    )
    if workspace is None:
        logger.error("  [bold red]✘[/bold red] Failed to create workspace")
        return None
    logger.info(f"  [bold green]✔[/bold green] Workspace [bold magenta]{workspace.id}[/bold magenta] created")
    return workspace.id


def update_workspace(api_instance, api_section: dict, payload: dict, workspace_id: str) -> bool:
    """Update an existing workspace and sync its security policy.

    ``workspace_id`` is passed explicitly it is no longer read from ``api_section``
    Returns False on failure.
    """
    logger.info(f"  [dim]→ Existing ID [bold cyan]{workspace_id}[/bold cyan] found. Updating...[/dim]")
    updated = api_instance.update_workspace(
        organization_id=api_section["organization_id"],
        workspace_id=workspace_id,
        workspace_update_request=WorkspaceUpdateRequest.from_dict(payload),
    )
    if updated is None:
        logger.error(f"  [bold red]✘[/bold red] Failed to update workspace {workspace_id}")
        return False
    if not sync_workspace_security(api_instance, api_section, payload, workspace_id):
        return False
    logger.info(f"  [bold green]✔[/bold green] Workspace [bold magenta]{workspace_id}[/bold magenta] updated")
    return True


def delete_api_resource(
    api_call: Callable[..., None],
    resource_name: str,
    org_id: str | None,
    resource_id: str,
    state: dict,
    state_key: str,
) -> None:
    """Delete a Cosmotech API resource and clear its ID from state.

    Handles the repetitive deletion pattern shared across organization, solution
    and workspace teardown.  A 404 response is treated as a no-op (already gone).
    """
    if not resource_id:
        logger.warning(f"  [yellow]⚠[/yellow] [dim]No {resource_name} ID found in state! skipping deletion[dim]")
        return

    try:
        logger.info(f"  [dim]→ Existing ID [bold cyan]{resource_id}[/bold cyan] found. Deleting...[/dim]")
        if org_id and resource_name != "Organization":
            api_call(organization_id=org_id, **{f"{resource_name.lower()}_id": resource_id})
        else:
            api_call(organization_id=resource_id)

        logger.info(f"  [bold green]✔[/bold green] {resource_name} [magenta]{resource_id}[/magenta] deleted")
        state["services"]["api"][state_key] = ""
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "Not Found" in error_msg:
            logger.info(f"  [bold yellow]⚠[/bold yellow] {resource_name} [magenta]{resource_id}[/magenta] already deleted (404)")
            state["services"]["api"][state_key] = ""
        else:
            logger.error(f"  [bold red]✘[/bold red] Error deleting {resource_name.lower()} {resource_id} reason: {e}")


def _get_existing_workspace_id(state: dict, payload: dict) -> Tuple[str, str | None]:
    """Helper to extract existing workspace ID and key from the state."""
    workspace_key = payload.get("key", "")
    ws_key = f"workspace-{workspace_key}" if workspace_key else None

    workspaces = state.get("workspaces", {})

    # Primary lookup
    if ws_key and ws_key in workspaces:
        existing_id = workspaces[ws_key].get("api", {}).get("workspace_id", "")
        if existing_id:
            return existing_id, ws_key

    # Fallback lookup
    for current_ws_key, current_ws_val in workspaces.items():
        current_id = current_ws_val.get("api", {}).get("workspace_id", "")
        if current_id and workspace_key and workspace_key == current_ws_key.removeprefix("workspace-"):
            return current_id, current_ws_key

    return "", ws_key
# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def sync_workspace_security(api_instance, api_section: dict, payload: dict, workspace_id: str) -> bool:
    """Synchronise security roles if a security block is present in the payload.

    ``workspace_id`` is passed explicitly.
    """
    if not payload.get("security"):
        return True
    try:
        logger.info("  [dim]→ Syncing security policies...[/dim]")
        current_security = api_instance.get_workspace_security(
            organization_id=api_section["organization_id"],
            workspace_id=workspace_id,
        )
        update_object_security(
            "workspace",
            current_security=current_security,
            desired_security=WorkspaceSecurity.from_dict(payload.get("security")),
            api_instance=api_instance,
            object_id=[api_section["organization_id"], workspace_id],
        )
        return True
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Security update failed: {e}")
        return False
