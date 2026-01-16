from logging import getLogger
from typing import Callable

from click import command, echo, option, style

from Babylon.commands.api.organization import get_organization_api_instance
from Babylon.commands.api.solution import get_solution_api_instance
from Babylon.commands.api.workspace import get_workspace_api_instance
from Babylon.commands.macro.deploy import resolve_inclusion_exclusion
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def _delete_resource(
    api_call: Callable[..., None], resource_name: str, org_id: str | None, resource_id: str, state: dict, state_key: str
):
    """Helper to handle repetitive deletion logic and error handling."""
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
        logger.error(f"  [bold red]✘[/bold red]] Error deleting {resource_name.lower()} {resource_id} reason: {e}")


@command()
@injectcontext()
@retrieve_state
@option("--include", "include", multiple=True, type=str, help="Specify the resources to destroy.")
@option("--exclude", "exclude", multiple=True, type=str, help="Specify the resources to exclude from destroction.")
def destroy(
    state: dict,
    include: tuple[str],
    exclude: tuple[str],
):
    """Macro Destroy"""
    organization, solution, workspace = resolve_inclusion_exclusion(include, exclude)
    # Header for the destructive operation
    echo(style(f"\n🔥 Starting Destruction Process in namespace: {env.environ_id}", bold=True, fg="red"))
    keycloak_token, config = get_keycloak_token()

    # We need the Org ID for most sub-resource deletions
    api_state = state["services"]["api"]
    org_id = api_state["organization_id"]

    # 1. Targeted Deletions using the helper
    if solution:
        api = get_solution_api_instance(config=config, keycloak_token=keycloak_token)
        _delete_resource(api.delete_solution, "Solution", org_id, api_state["solution_id"], state, "solution_id")
    if workspace:
        api = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)
        _delete_resource(api.delete_workspace, "Workspace", org_id, api_state["workspace_id"], state, "workspace_id")

    if organization:
        api = get_organization_api_instance(config=config, keycloak_token=keycloak_token)
        _delete_resource(api.delete_organization, "Organization", None, org_id, state, "organization_id")

    # --- State Persistence ---
    env.store_state_in_local(state=state)
    if state.get("remote"):
        logger.info("  [dim]☁ Syncing state cleanup to cloud...[/dim]")
        env.set_blob_client()
        env.store_state_in_cloud(state=state)

    # --- Final Destruction Summary ---
    echo(style("\n📋 Destruction Summary", bold=True, fg="white"))
    final_state = env.get_state_from_local()
    services = final_state.get("services")
    api_data = services.get("api")
    for key, value in api_data.items():
        # Prepare the label (e.g., "Organization Id")
        label_text = f"  • {key.replace('_', ' ').title()}"
        # We check if the ID is now empty (which means it was deleted)
        status = "DELETED" if not value else value
        color = "red" if status == "DELETED" else "green"

        styled_label = style(f"{label_text:<20}:", fg="cyan", bold=True)
        styled_status = style(status, fg=color)
        echo(f"{styled_label} {styled_status}")

    echo(style("\n✨ Cleanup process complete", fg="white", bold=True))
    return CommandResponse.success()
