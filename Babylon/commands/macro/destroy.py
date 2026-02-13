import subprocess
from logging import getLogger
from pathlib import Path
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


def _destroy_webapp(state: dict):
    """Run the Terraform destroy process for WebApp resources"""
    logger.info("  [dim]→ Running Terraform destroy for WebApp resources...[/dim]")
    webapp_state = state.get("services", {}).get("webapp", {})
    webapp_neme = webapp_state.get("webapp_name")
    if not webapp_neme:
        logger.warning("  [yellow]⚠[/yellow] [dim]No WebApp found in state! skipping deletion [dim]")
        return
    tf_dir = Path(str(env.working_dir)).parent / "terraform-webapp"

    if not tf_dir.exists():
        logger.error(f"  [bold red]✘[/bold red] Terraform directory not found at {tf_dir}")
        return
    try:
        process = subprocess.Popen(
            ["terraform", "destroy", "-auto-approve"],
            cwd=tf_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        
        line_handlers = {
            "Destroy complete!": "green",
            "Resources:": "green",
            "Error": "red",
        }
        
        for line in process.stdout:
            clean_line = line.strip()
            if not clean_line:
                continue
            
            color = next((color for key, color in line_handlers.items() if key in clean_line), "white")
            bold = color == "red"
            echo(style(f"   {clean_line}", fg=color, bold=bold))

        process.wait()
        if process.returncode == 0:
            # Nettoyage du state webapp
            state["services"]["webapp"]["webapp_name"] = ""
            state["services"]["webapp"]["webapp_url"] = ""
            logger.info(f"   [green]✔[/green] WebApp [magenta]{webapp_neme}[/magenta] destroyed")
        else:
            logger.error(f"  [bold red]✘[/bold red] Terraform destroy failed (Code {process.returncode})")

    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Error during WebApp destruction: {e}")


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
        error_msg = str(e)
        if "404" in error_msg or "Not Found" in error_msg:
            logger.info(
                f"  [bold yellow]⚠[/bold yellow] {resource_name} [magenta]{resource_id}[/magenta] already deleted (404)"
            )
            state["services"]["api"][state_key] = ""
        else:
            logger.error(f"  [bold red]✘[/bold red] Error deleting {resource_name.lower()} {resource_id} reason: {e}")


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
    organization, solution, workspace, webapp = resolve_inclusion_exclusion(include, exclude)
    # Header for the destructive operation
    echo(style(f"\n🔥 Starting Destruction Process in namespace: {env.environ_id}", bold=True, fg="red"))
    keycloak_token, config = get_keycloak_token()

    # We need the Org ID for most sub-resource deletions
    api_state = state["services"]["api"]
    org_id = api_state["organization_id"]

    if solution:
        api = get_solution_api_instance(config=config, keycloak_token=keycloak_token)
        _delete_resource(api.delete_solution, "Solution", org_id, api_state["solution_id"], state, "solution_id")
    if workspace:
        api = get_workspace_api_instance(config=config, keycloak_token=keycloak_token)
        _delete_resource(api.delete_workspace, "Workspace", org_id, api_state["workspace_id"], state, "workspace_id")

    if organization:
        api = get_organization_api_instance(config=config, keycloak_token=keycloak_token)
        _delete_resource(api.delete_organization, "Organization", None, org_id, state, "organization_id")

    if webapp:
        _destroy_webapp(state)

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
        echo(f"{style(f'{label_text:<20}:', fg='cyan', bold=True)} {style(status, fg=color)}")

    # Affichage WebApp
    webapp_data = services.get("webapp", {})
    webapp_id = webapp_data.get("webapp_name")
    label_text = "  • Webapp Name"
    status = "DELETED" if not webapp_id else webapp_id
    color = "red" if status == "DELETED" else "green"
    echo(f"{style(f'{label_text:<20}:', fg='cyan', bold=True)} {style(status, fg=color)}")

    echo(style("\n✨ Cleanup process complete", fg="white", bold=True))
    return CommandResponse.success()
