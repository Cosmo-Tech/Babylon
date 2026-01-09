from logging import getLogger

from click import Path, argument, group, option
from cosmotech_api import ApiClient, Configuration, SolutionApi
from cosmotech_api.models.solution_create_request import SolutionCreateRequest
from cosmotech_api.models.solution_update_request import SolutionUpdateRequest
from yaml import safe_load

from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


def get_solution_api_instance(config: dict, keycloak_token: str) -> SolutionApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return SolutionApi(api_client)


@group()
def solutions():
    """Solution - Cosmotech API"""
    pass


@solutions.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@argument("payload_file", type=Path(exists=True))
def create(config: dict, keycloak_token: str, organization_id: str, payload_file) -> CommandResponse:
    """
    Create a solution using a YAML payload file.
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    solution_create_request = SolutionCreateRequest.from_dict(payload)
    api_instance = get_solution_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        solution = api_instance.create_solution(organization_id, solution_create_request)

        if not solution:
            logger.error("  [bold red]✘[/bold red] API returned no data.")
            return CommandResponse.fail()

        logger.info(f"  [bold green]✔[/bold green] Solution [bold cyan]{solution.id}[/bold cyan] successfully created")
        return CommandResponse.success(solution.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Creation Failed Reason: {e}")
        return CommandResponse.fail()


@solutions.command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--sid", "solution_id", required=True, type=str, help="Solution ID")
def delete(config: dict, keycloak_token: str, organization_id: str, solution_id: str) -> CommandResponse:
    """Delete a solution by ID"""
    api_instance = get_solution_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        api_instance.delete_solution(organization_id=organization_id, solution_id=solution_id)
        logger.info(f"  [bold green]✔[/bold green] Solution [bold red]{solution_id}[/bold red] successfully deleted")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Deletion Failed Reason: {e}")
        return CommandResponse.fail()


@solutions.command("list")
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
def list_solutions(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """List solutions"""
    api_instance = get_solution_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        solutions = api_instance.list_solutions(organization_id=organization_id)
        count = len(solutions)
        logger.info(f"  [green]✔[/green] [bold]{count}[/bold] Solution(s) retrieved successfully")
        data_list = [ds.model_dump() for ds in solutions]
        return CommandResponse.success(data_list)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Failed Reason: {e}")
        return CommandResponse.fail()


@solutions.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--sid", "solution_id", required=True, type=str, help="Solution ID")
def get(config: dict, keycloak_token: str, organization_id: str, solution_id: str) -> CommandResponse:
    """Get solution"""
    api_instance = get_solution_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        solution = api_instance.get_solution(organization_id=organization_id, solution_id=solution_id)
        logger.info(f"  [green]✔[/green] Solution [bold cyan]{solution.id}[/bold cyan] retrieved successfully")
        return CommandResponse.success({solution.id: solution.model_dump()})
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Solution Failed Reason: {e}")
        return CommandResponse.fail()


@solutions.command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--sid", "solution_id", required=True, type=str, help="Solution ID")
@argument("payload_file", type=Path(exists=True))
def update(config: dict, keycloak_token: str, organization_id: str, solution_id: str, payload_file) -> CommandResponse:
    """Update solution"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    solution_update_request = SolutionUpdateRequest.from_dict(payload)
    api_instance = get_solution_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        updated = api_instance.update_solution(
            organization_id=organization_id,
            solution_id=solution_id,
            solution_update_request=solution_update_request,
        )
        logger.info(f"  [green]✔[/green] Solution [bold cyan]{updated.id}[/bold cyan] updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Update Solution Failed Reason: {e}")
        return CommandResponse.fail()
