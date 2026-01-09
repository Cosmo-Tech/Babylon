from logging import getLogger

from click import group, option
from cosmotech_api import ApiClient, Configuration, RunApi

from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


def get_run_api_instance(config: dict, keycloak_token: str) -> RunApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return RunApi(api_client)


@group()
def runs():
    """Run - Cosmotech API"""
    pass


@runs.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
@option("--rnid", "run_id", required=True, type=str, help="Run ID")
def get(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, run_id: str
) -> CommandResponse:
    """Get a run"""
    api_instance = get_run_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        run = api_instance.get_run(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
            run_id=run_id,
        )
        logger.info(f"  [green]✔[/green] Run [bold cyan]{run.id}[/bold cyan] retrieved successfully")
        return CommandResponse.success(run.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not get run: {e}")
        return CommandResponse.fail()


@runs.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
@option("--rnid", "run_id", required=True, type=str, help="Run ID")
def delete(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, run_id: str
) -> CommandResponse:
    """Delete a run"""
    api_instance = get_run_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        api_instance.delete_run(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
            run_id=run_id,
        )
        logger.info(f"  [green]✔[/green] Run [bold red]{run_id}[/bold red] deleted successfully")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not delete run: {e}")
        return CommandResponse.fail()


@runs.command("list")
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
def list_runs(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """List runs"""
    api_instance = get_run_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        runs = api_instance.list_runs(organization_id=organization_id, workspace_id=workspace_id, runner_id=runner_id)
        count = len(runs)
        logger.info(f"  [green]✔[/green] [bold]{count}[/bold] Run(s) retrieved successfully")
        data_list = [ds.model_dump() for ds in runs]
        return CommandResponse.success(data_list)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not list runs: {e}")
        return CommandResponse.fail()


@runs.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
@option("--rnid", "run_id", required=True, type=str, help="Run ID")
def get_logs(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, run_id: str
) -> CommandResponse:
    """Get run logs"""
    api_instance = get_run_api_instance(config, keycloak_token)
    try:
        logger.info(f"  [green]✔[/green] Fetching logs for Run [magenta]{run_id}[/magenta]")
        logger.info(f"  [dim]→ Runner ID: {runner_id}[/dim]")
        logger.info("  [dim]→ Sending request to API...[/dim]")
        logs = api_instance.get_run_logs(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
            run_id=run_id,
        )
        logger.info(f"  [green]✔[/green] Run logs retrieved successfully {logs}")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not get run logs: {e}")
        return CommandResponse.fail()


@runs.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
@option("--rnid", "run_id", required=True, type=str, help="Run ID")
def get_status(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, run_id: str
) -> CommandResponse:
    """Get run status"""
    api_instance = get_run_api_instance(config, keycloak_token)
    try:
        logger.info(f"  [green]✔[/green] Checking status for Run [magenta]{run_id}[/magenta]")
        logger.info(f"  [dim]→ Runner ID: {runner_id}[/dim]")
        logger.info("  [dim]→ Sending request to API...[/dim]")
        status = api_instance.get_run_status(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
            run_id=run_id,
        )
        logger.info(f"  [green]✔[/green] Run status retrieved successfully is [bold cyan]{status.phase}[/bold cyan]")
        return CommandResponse.success(status.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not get run status: {e}")
        return CommandResponse.fail()
