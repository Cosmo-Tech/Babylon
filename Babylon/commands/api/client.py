from logging import getLogger

from click import Path, argument, command, option
from cosmotech_api import (
    ApiClient,
    Configuration,
    DatasetApi,
    MetaApi,
    OrganizationApi,
    RunApi,
    RunnerApi,
    SolutionApi,
    WorkspaceApi,
)
from cosmotech_api.models.about_info import AboutInfo
from cosmotech_api.models.dataset_create_request import DatasetCreateRequest
from cosmotech_api.models.dataset_part_create_request import DatasetPartCreateRequest
from cosmotech_api.models.dataset_part_update_request import DatasetPartUpdateRequest
from cosmotech_api.models.dataset_update_request import DatasetUpdateRequest
from cosmotech_api.models.organization_create_request import OrganizationCreateRequest
from cosmotech_api.models.organization_update_request import OrganizationUpdateRequest
from cosmotech_api.models.runner_create_request import RunnerCreateRequest
from cosmotech_api.models.runner_update_request import RunnerUpdateRequest
from cosmotech_api.models.solution_create_request import SolutionCreateRequest
from cosmotech_api.models.solution_update_request import SolutionUpdateRequest
from cosmotech_api.models.workspace_create_request import WorkspaceCreateRequest
from cosmotech_api.models.workspace_update_request import WorkspaceUpdateRequest
from yaml import safe_load

from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


def get_organization_api_instance(config: dict, keycloak_token: str) -> OrganizationApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return OrganizationApi(api_client)


def get_solution_api_instance(config: dict, keycloak_token: str) -> SolutionApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return SolutionApi(api_client)


def get_workspace_api_instance(config: dict, keycloak_token: str) -> WorkspaceApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return WorkspaceApi(api_client)


def get_dataset_api_instance(config: dict, keycloak_token: str) -> DatasetApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return DatasetApi(api_client)


def get_runner_api_instance(config: dict, keycloak_token: str) -> RunnerApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return RunnerApi(api_client)


def get_run_api_instance(config: dict, keycloak_token: str) -> RunApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return RunApi(api_client)


def get_meta_api_instance(config: dict, keycloak_token: str) -> MetaApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return MetaApi(api_client)


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("payload_file", type=Path(exists=True))
def create_organization(config: dict, keycloak_token: str, payload_file) -> CommandResponse:
    """
    Create an organization using a YAML payload file.
    """
    # Load and parse the payload
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    # Initialize API
    organization_create_request = OrganizationCreateRequest.from_dict(payload)
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        organization = api_instance.create_organization(organization_create_request)

        if not organization:
            logger.error("  [bold red]✘[/bold red] API returned no data.")
            return CommandResponse.fail()

        logger.info(
            f"  [bold green]✔[/bold green] Organization [bold cyan]{organization.id}[/bold cyan] successfully created"
        )
        return CommandResponse.success(organization.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Creation Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@argument("payload_file", type=Path(exists=True))
def create_dataset(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, payload_file
) -> CommandResponse:
    """
    Create a dataset using a YAML payload file.
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_create_request = DatasetCreateRequest.from_dict(payload)
    file_contents_list = [part["sourceName"] for part in payload["parts"]]
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        dataset = api_instance.create_dataset(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_create_request=dataset_create_request,
            files=file_contents_list,
        )
        if not dataset:
            logger.error("  [bold red]✘[/bold red] API returned no data.")
            return CommandResponse.fail()

        logger.info(f"  [bold green]✔[/bold green] Dataset [bold cyan]{dataset.id}[/bold cyan] successfully created")
        return CommandResponse.success(dataset.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Creation Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@argument("payload_file", type=Path(exists=True))
def create_solution(config: dict, keycloak_token: str, organization_id: str, payload_file) -> CommandResponse:
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


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--sid", "solution_id", required=True, type=str, help="Solution ID")
@argument("payload_file", type=Path(exists=True))
def create_workspace(
    config: dict, keycloak_token: str, organization_id: str, solution_id: str, payload_file
) -> CommandResponse:
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


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--sid", "solution_id", required=True, type=str, help="Solution ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@argument("payload_file", type=Path(exists=True))
def create_runner(
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
        logger.info("  [dim]→ Sending request to API...[/dim]")
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


@command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
def delete_organization(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """
    Delete an organization by ID
    """
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        # API Execution
        logger.info("  [dim]→ Sending request to API...[/dim]")
        api_instance.delete_organization(organization_id)
        logger.info(
            f"  [bold green]✔[/bold green] Organization [bold red]{organization_id}[/bold red] successfully deleted"
        )
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Deletion Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
def list_organizations(config: dict, keycloak_token: str) -> CommandResponse:
    """
    List all organizations
    """
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        organizations = api_instance.list_organizations()
        count = len(organizations)
        logger.info(f"  [green]✔[/green] [bold]{count}[/bold] organization(s) retrieved successfully")
        data_list = [org.model_dump() for org in organizations]
        return CommandResponse.success(data_list)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Failed Reason: {e}")
        return CommandResponse.fail()


@command()
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


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
def list_datasets(config: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
    """
    List all datasets
    """
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        datasets = api_instance.list_datasets(organization_id=organization_id, workspace_id=workspace_id)
        count = len(datasets)
        logger.info(f"  [green]✔[/green] [bold]{count}[/bold] Dataset(s) retrieved successfully")
        data_list = [ds.model_dump() for ds in datasets]
        return CommandResponse.success(data_list)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--sid", "solution_id", required=True, type=str, help="Solution ID")
def delete_solution(config: dict, keycloak_token: str, organization_id: str, solution_id: str) -> CommandResponse:
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


@command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
def delete_workspace(config: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
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


@command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
def delete_runner(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """Delete a runner by ID"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        api_instance.delete_runner(organization_id=organization_id, workspace_id=workspace_id, runner_id=runner_id)
        logger.info(f"  [bold green]✔[/bold green] Runner [bold red]{runner_id}[/bold red] successfully deleted")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Deletion Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
def delete_dataset(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str
) -> CommandResponse:
    """Delete a dataset by ID"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        api_instance.delete_dataset(organization_id=organization_id, workspace_id=workspace_id, dataset_id=dataset_id)
        logger.info(f"  [bold green]✔[/bold green] Dataset [bold red]{dataset_id}[/bold red] successfully deleted")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Deletion Failed Reason: {e}")
        return CommandResponse.fail()


@command()
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


@command()
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
        logger.info("  [dim]→ Sending request to API...[/dim]")
        runners = api_instance.list_runners(organization_id=organization_id, workspace_id=workspace_id)
        count = len(runners)
        logger.info(f"  [green]✔[/green] [bold]{count}[/bold] Runner(s) retrieved successfully")
        data_list = [ds.model_dump() for ds in runners]
        return CommandResponse.success(data_list)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
def get_organization(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """Get organization"""
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        organization = api_instance.get_organization(organization_id=organization_id)
        logger.info(f"  [green]✔[/green] Organization [bold cyan]{organization.id}[/bold cyan] retrieved successfully")
        return CommandResponse.success({organization.id: organization.model_dump()})
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Organization Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
def get_workspace(config: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
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


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--sid", "solution_id", required=True, type=str, help="Solution ID")
def get_solution(config: dict, keycloak_token: str, organization_id: str, solution_id: str) -> CommandResponse:
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


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
def get_dataset(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str
) -> CommandResponse:
    """Get dataset"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        dataset = api_instance.get_dataset(
            organization_id=organization_id, workspace_id=workspace_id, dataset_id=dataset_id
        )
        logger.info(f"  [green]✔[/green] Dataset [bold cyan]{dataset.id}[/bold cyan] retrieved successfully")
        return CommandResponse.success(dataset.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Dataset Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
def get_runner(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """Get runner"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        runner = api_instance.get_runner(
            organization_id=organization_id, workspace_id=workspace_id, runner_id=runner_id
        )
        logger.info(f"  [green]✔[/green] Runner [bold cyan]{runner.id}[/bold cyan] retrieved successfully")
        return CommandResponse.success(runner.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Runner Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@argument("payload_file", type=Path(exists=True))
def update_organization(config: dict, keycloak_token: str, organization_id: str, payload_file) -> CommandResponse:
    """
    Update organization
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    organization_update_request = OrganizationUpdateRequest.from_dict(payload)
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        updated = api_instance.update_organization(
            organization_id=organization_id, organization_update_request=organization_update_request
        )
        logger.info(f"  [green]✔[/green] Organization [bold cyan]{updated.id}[/bold cyan] updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Update Organization Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@argument("payload_file", type=Path(exists=True))
def update_workspace(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, payload_file
) -> CommandResponse:
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


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--sid", "solution_id", required=True, type=str, help="Solution ID")
@argument("payload_file", type=Path(exists=True))
def update_solution(
    config: dict, keycloak_token: str, organization_id: str, solution_id: str, payload_file
) -> CommandResponse:
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


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@argument("payload_file", type=Path(exists=True))
def update_dataset(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, payload_file
) -> CommandResponse:
    """Update dataset"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_update_request = DatasetUpdateRequest.from_dict(payload)
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        updated = api_instance.update_dataset(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_update_request=dataset_update_request,
            files=[part["sourceName"] for part in payload["parts"]],
        )
        logger.info(f"  [green]✔[/green] Dataset [bold cyan]{updated.id}[/bold cyan] updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Update Dataset Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
@argument("payload_file", type=Path(exists=True))
def update_runner(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, payload_file
) -> CommandResponse:
    """Update runner"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    runner_update_request = RunnerUpdateRequest.from_dict(payload)
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
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


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
def about(config: dict, keycloak_token: str) -> CommandResponse:
    """Get API about information"""
    api_instance = get_meta_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        about_info: AboutInfo = api_instance.about()
        logger.info(f"  [green]✔[/green] API About Information: {about_info}")
        return CommandResponse.success(about_info.to_dict())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not retrieve about information: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@argument("payload_file", type=Path(exists=True))
def create_dataset_part(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, payload_file
) -> CommandResponse:
    """Create dataset part"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_part_create_request = DatasetPartCreateRequest.from_dict(payload)
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        created = api_instance.create_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_create_request=dataset_part_create_request,
            file=payload["sourceName"],
        )
        if not created:
            logger.error("  [bold red]✘ API returned no data.[/bold red]")
            return CommandResponse.fail()
        logger.info(f"  [bold green]✔[/bold green] Dataset [bold cyan]{created.id}[/bold cyan] successfully created")
        return CommandResponse.success(created.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Creation Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
def list_dataset_parts(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str
) -> CommandResponse:
    """List dataset parts"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        dataset_parts = api_instance.list_dataset_parts(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
        )
        count = len(dataset_parts)
        logger.info(f"  [green]✔[/green] [bold]{count}[/bold] Dataset parts retrieved successfully")
        data_list = [ds.model_dump() for ds in dataset_parts]
        return CommandResponse.success(data_list)
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
def get_dataset_part(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, dataset_part_id: str
) -> CommandResponse:
    """Get dataset part"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        dataset_part = api_instance.get_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
        )
        logger.info(f"  [green]✔[/green] Dataset parts [bold]{dataset_part.id}[/bold] retrieved successfully")
        return CommandResponse.success(dataset_part.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Retrieve Dataset part Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
def delete_dataset_part(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, dataset_part_id: str
) -> CommandResponse:
    """Delete dataset part by ID"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        api_instance.delete_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
        )
        logger.info(f"  [green]✔[/green] Dataset parts [bold]{dataset_part_id}[/bold] successfully deleted")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Deletion Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
@argument("payload_file", type=Path(exists=True))
def update_dataset_part(
    config: dict,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    dataset_id: str,
    dataset_part_id: str,
    payload_file,
) -> CommandResponse:
    """Update dataset part"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_part_update_request = DatasetPartUpdateRequest.from_dict(payload)
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        updated = api_instance.update_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
            dataset_part_update_request=dataset_part_update_request,
        )
        logger.info(f"  [green]✔[/green] Dataset part [bold cyan]{updated.id}[/bold cyan] updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Update Runner Failed Reason: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
@option(
    "--selects",
    type=str,
    multiple=True,
    help="Column names that should be part of the response data.",
)
@option(
    "--sums",
    type=str,
    multiple=True,
    help="Column names to sum by.",
)
@option(
    "--avgs",
    type=str,
    multiple=True,
    help="Column names to average by.",
)
@option(
    "--counts",
    type=str,
    multiple=True,
    help="Column names to count by.",
)
@option(
    "--mins",
    type=str,
    multiple=True,
    help="Column names to min by.",
)
@option(
    "--maxs",
    type=str,
    multiple=True,
    help="Column names to max by.",
)
@option("--offset", type=int, help="The query offset")
@option("--limit", type=int, help="The query limit")
@option("--group-bys", type=str, multiple=True, help="Column names to group by")
@option(
    "--order-bys",
    type=str,
    multiple=True,
    help="Column names to order by. Default order is ascending.",
)
def query_data(
    config: dict,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    dataset_id: str,
    dataset_part_id: str,
    selects: tuple,
    sums: tuple,
    avgs: tuple,
    counts: tuple,
    mins: tuple,
    maxs: tuple,
    offset: int,
    limit: int,
    group_bys: tuple,
    order_bys: tuple,
) -> CommandResponse:
    """Query data from a dataset part"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending query to API...[/dim]")
        query_result = api_instance.query_data(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
            selects=list(selects) if selects else None,
            sums=list(sums) if sums else None,
            avgs=list(avgs) if avgs else None,
            counts=list(counts) if counts else None,
            mins=list(mins) if mins else None,
            maxs=list(maxs) if maxs else None,
            offset=offset,
            limit=limit,
            group_bys=list(group_bys) if group_bys else None,
            order_bys=list(order_bys) if order_bys else None,
        )
        logger.info(f"  [green]✔[/green] Query result: {query_result}")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not query data: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
def start_run(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """Start a run"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
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


@command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
def stop_run(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """Stop a run"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        api_instance.stop_run(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
        )
        logger.info(f"  [green]✔[/green] Run [bold cyan]{runner_id}[/bold cyan] stopped successfully")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not stop run: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
@option("--rnid", "run_id", required=True, type=str, help="Run ID")
def get_run(
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


@command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
@option("--rnid", "run_id", required=True, type=str, help="Run ID")
def delete_run(
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
        logger.info(f"  [green]✔[/green] Run {run_id} deleted successfully")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not delete run: {e}")
        return CommandResponse.fail()


@command()
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
        logger.error(f"   [bold red]✘[/bold red] Could not list runs: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
@option("--rnid", "run_id", required=True, type=str, help="Run ID")
def get_run_logs(
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


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--rid", "runner_id", required=True, type=str, help="Runner ID")
@option("--rnid", "run_id", required=True, type=str, help="Run ID")
def get_run_status(
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


@command()
@injectcontext()
@pass_keycloak_token()
@option("--oid", "organization_id", required=True, type=str, help="Organization ID")
@option("--wid", "workspace_id", required=True, type=str, help="Workspace ID")
@option("--did", "dataset_id", required=True, type=str, help="Dataset ID")
@option("--dpid", "dataset_part_id", required=True, type=str, help="Dataset Part ID")
def download_dataset_part(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, dataset_part_id: str
) -> CommandResponse:
    """Download dataset part"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        logger.info("  [dim]→ Sending request to API...[/dim]")
        file_content = api_instance.download_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
        )
        with open(dataset_part_id, "wb") as f:
            f.write(file_content)
        logger.info(f"  [green]✔[/green] Dataset part downloaded successfully to {dataset_part_id}")
        return CommandResponse.success({"file_path": dataset_part_id})
    except Exception as e:
        logger.error(f"  [bold red]✘[/bold red] Could not download dataset part: {e}")
        return CommandResponse.fail()
