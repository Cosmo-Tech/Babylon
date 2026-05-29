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

logger = getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_workspace(api_instance, api_section: dict, payload: dict, state: dict) -> bool:
    """Create a new workspace and persist its ID in state. Returns False on failure."""
    logger.info("  [dim]→ No existing workspace ID found. Creating...[/dim]")
    workspace = api_instance.create_workspace(
        organization_id=api_section["organization_id"],
        workspace_create_request=WorkspaceCreateRequest.from_dict(payload),
    )
    if workspace is None:
        logger.error("  [bold red]✘[/bold red] Failed to create workspace")
        return False
    logger.info(f"  [bold green]✔[/bold green] Workspace [bold magenta]{workspace.id}[/bold magenta] created")
    state["services"]["api"]["workspace_id"] = workspace.id
    return True


def update_workspace(api_instance, api_section: dict, payload: dict) -> bool:
    """Update an existing workspace and sync its security policy. Returns False on failure."""
    logger.info(f"  [dim]→ Existing ID [bold cyan]{api_section['workspace_id']}[/bold cyan] found. Updating...[/dim]")
    updated = api_instance.update_workspace(
        organization_id=api_section["organization_id"],
        workspace_id=api_section["workspace_id"],
        workspace_update_request=WorkspaceUpdateRequest.from_dict(payload),
    )
    if updated is None:
        logger.error(f"  [bold red]✘[/bold red] Failed to update workspace {api_section['workspace_id']}")
        return False
    if not sync_workspace_security(api_instance, api_section, payload):
        return False
    logger.info(f"  [bold green]✔[/bold green] Workspace [bold magenta]{api_section['workspace_id']}[/bold magenta] updated")
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
            logger.info(
                f"  [bold yellow]⚠[/bold yellow] {resource_name} [magenta]{resource_id}[/magenta] already deleted (404)"
            )
            state["services"]["api"][state_key] = ""
        else:
            logger.error(f"  [bold red]✘[/bold red] Error deleting {resource_name.lower()} {resource_id} reason: {e}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def sync_workspace_security(api_instance, api_section: dict, payload: dict) -> bool:
    """Synchronise security roles if a security block is present in the payload."""
    if not payload.get("security"):
        return True
    try:
        logger.info("  [dim]→ Syncing security policies...[/dim]")
        current_security = api_instance.get_workspace_security(
            organization_id=api_section["organization_id"],
            workspace_id=api_section["workspace_id"],
        )
        update_object_security(
            "workspace",
            current_security=current_security,
            desired_security=WorkspaceSecurity.from_dict(payload.get("security")),
            api_instance=api_instance,
            object_id=[api_section["organization_id"], api_section["workspace_id"]],
        )
        return True
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Security update failed: {e}")
        return False
