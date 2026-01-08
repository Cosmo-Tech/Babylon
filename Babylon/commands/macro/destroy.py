from logging import getLogger

from click import command, echo, option, style

from Babylon.commands.api.client import (
    get_organization_api_instance,
    get_solution_api_instance,
    get_workspace_api_instance,
)
from Babylon.commands.macro.deploy import resolve_inclusion_exclusion
from Babylon.utils.credentials import get_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


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

    # Initialize API clients
    organization_api_instance = get_organization_api_instance(config=config, keycloak_token=keycloak_token)
    workspace_api_instance = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)
    solution_api_instance = get_solution_api_instance(config=config, keycloak_token=keycloak_token)

    # We need the Org ID for most sub-resource deletions
    organization_id = state["services"]["api"]["organization_id"]

    # --- 1. Delete Solution ---
    if solution:
        solution_id = state["services"]["api"]["solution_id"]
        if solution_id:
            try:
                logger.info(f"  [dim]→ Existing ID [bold cyan]{solution_id}[/bold cyan] found. Deleting...[/dim]")
                solution_api_instance.delete_solution(organization_id=organization_id, solution_id=solution_id)
                logger.info(f"  [bold green]✔[/bold green] Solution [magenta]{solution_id}[/magenta] deleted")
                state["services"]["api"]["solution_id"] = ""
            except Exception as e:
                logger.error(f"  [bold red]✘[/bold red]] Error deleting solution {solution_id} reason: {e}")
        else:
            logger.warning("  [yellow]⚠[/yellow] [dim]No Solution ID found in state! skipping deletion[dim]")
    # --- 2. Delete Workspace ---
    if workspace:
        workspace_id = state["services"]["api"]["workspace_id"]
        if workspace_id:
            try:
                logger.info(f"  [dim]→ Existing ID [bold cyan]{workspace_id}[/bold cyan] found. Deleting...[/dim]")
                workspace_api_instance.delete_workspace(organization_id=organization_id, workspace_id=workspace_id)
                logger.info(f"  [bold green]✔[/bold green] Workspace [magenta]{workspace_id}[/magenta] deleted")
                state["services"]["api"]["workspace_id"] = ""
            except Exception as e:
                logger.error(f"  [bold red]✘[/bold red]] Error deleting workspace {workspace_id} reason: {e}")
        else:
            logger.warning("  [yellow]⚠[/yellow] [dim]No Workspace ID found in state! skipping deletion[dim]")
    # --- 3. Delete Organization ---
    if organization:
        if organization_id:
            try:
                logger.info(f"  [dim]→ Existing ID [bold cyan]{organization_id}[/bold cyan] found. Deleting...[/dim]")
                organization_api_instance.delete_organization(organization_id=organization_id)
                logger.info(f"  [bold green]✔[/bold green] Organization [magenta]{organization_id}[/magenta] deleted")
                state["services"]["api"]["organization_id"] = ""
            except Exception as e:
                logger.error(f"  [bold red]✘[/bold red]] Error deleting organization {organization_id} reason: {e}")
        else:
            logger.warning("  [yellow]⚠[/yellow] [dim]No Organization ID found in state! skipping deletion[dim]")
    # --- State Persistence ---
    env.store_state_in_local(state=state)
    remote = state["remote"]
    if remote:
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
