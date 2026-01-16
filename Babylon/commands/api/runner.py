from logging import getLogger

from click import Path, argument, group, option
from cosmotech_api import ApiClient, Configuration, RunnerApi
from cosmotech_api.models.runner_create_request import RunnerCreateRequest
from cosmotech_api.models.runner_update_request import RunnerUpdateRequest
from yaml import safe_load

from Babylon.utils import API_REQUEST_MESSAGE
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


def get_runner_api_instance(config: dict, keycloak_token: str) -> RunnerApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return RunnerApi(api_client)


@group()
def runners():
    """Runner - Cosmotech API"""
    pass


@runners.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--sid", "solution_id", required=True, type=str, help="Solution ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@argument("payload_file", type=Path(exists=True))
def create(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, solution_id: str, payload_file
) -> CommandResponse:
    """
    Create a runner using a YAML payload file.
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)

    payload["solutionId"] = solution_id
    runner_create_request = RunnerCreateRequest.from_dict(payload)
    api_instance = get_runner_api_instance(config, keycloak_token)

    try:
        logger.info(API_REQUEST_MESSAGE)
        runner = api_instance.create_runner(
            organization_id=organization_id, workspace_id=workspace_id, runner_create_request=runner_create_request
        )
        if not runner:
            logger.error("  [bold red]✘[/bold red] API returned no data.")
            return CommandResponse.fail()

        logger.info(f"  [bold green]✔[/bold green] Runner [bold cyan]{runner.id}[/bold cyan] successfully created")
        return CommandResponse.success(runner.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Creation Failed Reason: {e}")
        return CommandResponse.fail()


@runners.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
def delete(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """Delete a runner by ID"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        api_instance.delete_runner(organization_id=organization_id, workspace_id=workspace_id, runner_id=runner_id)
        logger.info(f"  [bold green]✔[/bold green] Runner [bold red]{runner_id}[/bold red] successfully deleted")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Deletion Failed Reason: {e}")
        return CommandResponse.fail()


@runners.command("list")
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@retrieve_config
def list_runners(config: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
    """List runners"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        runners = api_instance.list_runners(organization_id=organization_id, workspace_id=workspace_id)
        count = len(runners)
        logger.info(f"  [green]✔[/green] [bold]{count}[/bold] Runner(s) retrieved successfully")
        data_list = [ds.model_dump() for ds in runners]
        return CommandResponse.success(data_list)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Failed Reason: {e}")
        return CommandResponse.fail()


@runners.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
def get(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str) -> CommandResponse:
    """Get runner"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        runner = api_instance.get_runner(
            organization_id=organization_id, workspace_id=workspace_id, runner_id=runner_id
        )
        logger.info(f"  [green]✔[/green] Runner [bold cyan]{runner.id}[/bold cyan] retrieved successfully")
        return CommandResponse.success(runner.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Runner Failed Reason: {e}")
        return CommandResponse.fail()


@runners.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
@argument("payload_file", type=Path(exists=True))
def update(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, payload_file
) -> CommandResponse:
    """Update runner"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    runner_update_request = RunnerUpdateRequest.from_dict(payload)
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        updated = api_instance.update_runner(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
            runner_update_request=runner_update_request,
        )
        logger.info(f"  [green]✔[/green] Runner [bold cyan]{updated.id}[/bold cyan] updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Update Runner Failed Reason: {e}")
        return CommandResponse.fail()


@runners.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
def start(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """Start a run"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        run = api_instance.start_run(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
        )
        logger.info(f"  [green]✔[/green] Run [bold cyan]{run.id}[/bold cyan] started successfully")
        return CommandResponse.success(run.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not start run: {e}")
        return CommandResponse.fail()


@runners.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
def stop(config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str) -> CommandResponse:
    """Stop a run"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        logger.info(API_REQUEST_MESSAGE)
        api_instance.stop_run(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
        )
        logger.info(f"  [green]✔[/green] Last run stopped successfully for runner [bold cyan]{runner_id}[/bold cyan]")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not stop run: {e}")
        return CommandResponse.fail()
