from logging import getLogger

from click import Path, argument, group, option
from cosmotech_api import ApiClient, Configuration, WorkspaceApi
from cosmotech_api.models.workspace_create_request import WorkspaceCreateRequest
from cosmotech_api.models.workspace_update_request import WorkspaceUpdateRequest
from yaml import safe_load

from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


def get_workspace_api_instance(config: dict, keycloak_token: str) -> WorkspaceApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return WorkspaceApi(api_client)


@group()
def workspaces():
    """Workspace - Cosmotech API"""
    pass


@workspaces.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--sid", "solution_id", required=True, type=str, help="Solution ID")
@argument("payload_file", type=Path(exists=True))
def create(config: dict, keycloak_token: str, organization_id: str, solution_id: str, payload_file) -> CommandResponse:
    """
    Create a workspace using a YAML payload file.
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)

    payload["solution"]["solutionId"] = solution_id
    workspace_create_request = WorkspaceCreateRequest.from_dict(payload)
    api_instance = get_workspace_api_instance(config, keycloak_token)

    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        workspace = api_instance.create_workspace(organization_id, workspace_create_request)
        if not workspace:
            logger.error("  [bold red]✘[/bold red] API returned no data.")
            return CommandResponse.fail()
        logger.info(
            f"  [bold green]✔[/bold green] Workspace [bold cyan]{workspace.id}[/bold cyan] successfully created"
        )
        return CommandResponse.success(workspace.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Creation Failed Reason: {e}")
        return CommandResponse.fail()


@workspaces.command("list")
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
def list_workspaces(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """
    List all workspaces
    """
    api_instance = get_workspace_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        workspaces = api_instance.list_workspaces(organization_id=organization_id)
        count = len(workspaces)
        logger.info(f"  [green]✔[/green] [bold]{count}[/bold] workspace(s) retrieved successfully")
        data_list = [ws.model_dump() for ws in workspaces]
        return CommandResponse.success(data_list)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Failed Reason: {e}")
        return CommandResponse.fail()


@workspaces.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
def delete(config: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
    """Delete a workspace by ID"""
    api_instance = get_workspace_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        api_instance.delete_workspace(organization_id=organization_id, workspace_id=workspace_id)
        logger.info(f"  [bold green]✔[/bold green] Workspace [bold red]{workspace_id}[/bold red] successfully deleted")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Deletion Failed Reason: {e}")
        return CommandResponse.fail()


@workspaces.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@argument("payload_file", type=Path(exists=True))
def update(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, payload_file) -> CommandResponse:
    """Update workspace"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    workspace_update_request = WorkspaceUpdateRequest.from_dict(payload)
    api_instance = get_workspace_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        updated = api_instance.update_workspace(
            organization_id=organization_id,
            workspace_id=workspace_id,
            workspace_update_request=workspace_update_request,
        )
        logger.info(f"  [green]✔[/green] Workspace [bold cyan]{updated.id}[/bold cyan] updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Update Workspace Failed Reason: {e}")
        return CommandResponse.fail()


@workspaces.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
def get(config: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
    """Get workspace"""
    api_instance = get_workspace_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        workspace = api_instance.get_workspace(organization_id=organization_id, workspace_id=workspace_id)
        logger.info(f"  [green]✔[/green] Workspace [bold cyan]{workspace.id}[/bold cyan] retrieved successfully")
        return CommandResponse.success({workspace.id: workspace.model_dump()})
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Workspace Failed Reason: {e}")
        return CommandResponse.fail()
