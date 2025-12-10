from logging import getLogger

from click import argument, command, option
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
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


def get_organization_api_instance(config: dict, keycloak_token: str) -> OrganizationApi:
    configuration = Configuration(host=config.get("api_url"))
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return OrganizationApi(api_client)


def get_solution_api_instance(config: dict, keycloak_token: str) -> SolutionApi:
    configuration = Configuration(host=config["api_url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return SolutionApi(api_client)


def get_workspace_api_instance(config: dict, keycloak_token: str) -> WorkspaceApi:
    configuration = Configuration(host=config["api_url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return WorkspaceApi(api_client)


def get_dataset_api_instance(config: dict, keycloak_token: str) -> DatasetApi:
    configuration = Configuration(host=config["api_url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return DatasetApi(api_client)


def get_runner_api_instance(config: dict, keycloak_token: str) -> RunnerApi:
    configuration = Configuration(host=config["api_url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return RunnerApi(api_client)


def get_run_api_instance(config: dict, keycloak_token: str) -> RunApi:
    configuration = Configuration(host=config["api_url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return RunApi(api_client)


def get_meta_api_instance(config: dict, keycloak_token: str) -> MetaApi:
    configuration = Configuration(host=config["api_url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return MetaApi(api_client)


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@argument("payload_file")
def create_organization(config: dict, keycloak_token: str, payload_file) -> CommandResponse:
    """
    Create organization
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    organization_create_request = OrganizationCreateRequest.from_dict(payload)
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        organization = api_instance.create_organization(organization_create_request)
        logger.info(f"Organization {organization.id} created successfully")
        return CommandResponse.success(organization.model_dump())
    except Exception as e:
        logger.error(f"Could not create organization: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@argument("payload_file")
def create_dataset(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, payload_file
) -> CommandResponse:
    """
    Create dataset
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_create_request = DatasetCreateRequest.from_dict(payload)
    file_contents_list = [part["sourceName"] for part in payload["parts"]]
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        dataset = api_instance.create_dataset(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_create_request=dataset_create_request,
            files=file_contents_list,
        )
        logger.info(f"Dataset {dataset.id} created successfully")
        return CommandResponse.success(dataset.model_dump())
    except Exception as e:
        logger.error(f"Could not create dataset: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@argument("payload_file")
def create_solution(config: dict, keycloak_token: str, organization_id: str, payload_file) -> CommandResponse:
    """
    Create solution
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    import json

    solution_create_request = SolutionCreateRequest.from_json(json.dumps(payload))

    api_instance = get_solution_api_instance(config, keycloak_token)
    try:
        solution = api_instance.create_solution(organization_id, solution_create_request)
        logger.info(f"Solution {solution.id} created successfully")
        return CommandResponse.success(solution.model_dump())
    except Exception as e:
        logger.error(f"Could not create solution: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--solution-id", "-sid", required=False, default=None, type=str, help="Solution ID")
@argument("payload_file")
def create_workspace(
    config: dict, keycloak_token: str, organization_id: str, solution_id: str, payload_file
) -> CommandResponse:
    """
    Create workspace
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    payload["solution"]["solutionId"] = solution_id
    workspace_create_request = WorkspaceCreateRequest.from_dict(payload)

    api_instance = get_workspace_api_instance(config, keycloak_token)
    try:
        workspace = api_instance.create_workspace(organization_id, workspace_create_request)
        logger.info(f"Workspace {workspace.id} created successfully")
        return CommandResponse.success(workspace.model_dump())
    except Exception as e:
        logger.error(f"Could not create workspace: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--solution-id", "-sid", required=False, default=None, type=str, help="Solution ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@argument("payload_file")
def create_runner(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, solution_id: str, payload_file
) -> CommandResponse:
    """
    Create runner
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    payload["solutionId"] = solution_id
    runner_create_request = RunnerCreateRequest.from_dict(payload)

    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        runner = api_instance.create_runner(
            organization_id=organization_id, workspace_id=workspace_id, runner_create_request=runner_create_request
        )
        logger.info(f"Runner {runner.id} created successfully")
        return CommandResponse.success(runner.model_dump())
    except Exception as e:
        logger.error(f"Could not create runner: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@argument("organization_id")
def delete_organization(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """
    Delete organization
    """
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        api_instance.delete_organization(organization_id)
        logger.info(f"Organization {organization_id} deleted successfully")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"Could not delete organization: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
def list_organizations(config: dict, keycloak_token: str) -> CommandResponse:
    """
    List organizations
    """
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        organizations = api_instance.list_organizations()
        logger.info(f"Organizations retrieved successfully {[org.id for org in organizations]}")
        return CommandResponse.success({org.id: org.model_dump() for org in organizations})
    except Exception as e:
        logger.error(f"Could not list organizations: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@retrieve_config
def list_workspaces(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """
    List workspaces
    """
    api_instance = get_workspace_api_instance(config, keycloak_token)
    try:
        workspaces = api_instance.list_workspaces(organization_id=organization_id)
        logger.info(f"Workspaces retrieved successfully {[workspace.id for workspace in workspaces]}")
        return CommandResponse.success({ws.id: ws.model_dump() for ws in workspaces})
    except Exception as e:
        logger.error(f"Could not list workspace: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@retrieve_config
def list_datasets(config: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
    """
    List datasets
    """
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        datasets = api_instance.list_datasets(organization_id=organization_id, workspace_id=workspace_id)
        logger.info(f"Datasets retrieved successfully {[dataset.id for dataset in datasets]}")
        return CommandResponse.success({ds.id: ds.model_dump() for ds in datasets})
    except Exception as e:
        logger.error(f"Could not list datasets: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@argument("solution_id")
def delete_solution(config: dict, keycloak_token: str, organization_id: str, solution_id: str) -> CommandResponse:
    """Delete solution"""
    api_instance = get_solution_api_instance(config, keycloak_token)
    try:
        api_instance.delete_solution(organization_id=organization_id, solution_id=solution_id)
        logger.info("Solution deleted successfully")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"Could not delete solution: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@argument("workspace_id")
def delete_workspace(config: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
    """Delete workspace"""
    api_instance = get_workspace_api_instance(config, keycloak_token)
    try:
        api_instance.delete_workspace(organization_id=organization_id, workspace_id=workspace_id)
        logger.info("Workspace deleted successfully")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"Could not delete workspace: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@argument("runner_id")
def delete_runner(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """Delete runner"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        api_instance.delete_runner(organization_id=organization_id, workspace_id=workspace_id, runner_id=runner_id)
        logger.info("Runner deleted successfully")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"Could not delete runner: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@argument("dataset_id")
def delete_dataset(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str
) -> CommandResponse:
    """Delete dataset"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        api_instance.delete_dataset(organization_id=organization_id, workspace_id=workspace_id, dataset_id=dataset_id)
        logger.info("Dataset deleted successfully")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"Could not delete dataset: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@retrieve_config
def list_solutions(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """List solutions"""
    api_instance = get_solution_api_instance(config, keycloak_token)
    try:
        solutions = api_instance.list_solutions(organization_id=organization_id)
        logger.info(f"Solutions retrieved successfully {[solution.id for solution in solutions]}")
        return CommandResponse.success({sol.id: sol.model_dump() for sol in solutions})
    except Exception as e:
        logger.error(f"Could not list solutions: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@retrieve_config
def list_runners(config: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
    """List runners"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        runners = api_instance.list_runners(organization_id=organization_id, workspace_id=workspace_id)
        logger.info(f"Runners retrieved successfully {[runner.id for runner in runners]}")
        return CommandResponse.success({runner.id: runner.model_dump() for runner in runners})
    except Exception as e:
        logger.error(f"Could not list runners: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@argument("organization-id")
def get_organization(config: dict, keycloak_token: str, organization_id: str) -> CommandResponse:
    """Get organization"""
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        organization = api_instance.get_organization(organization_id=organization_id)
        logger.info(f"Organization retrieved successfully {organization.id}")
        return CommandResponse.success({organization.id: organization.model_dump()})
    except Exception as e:
        logger.error(f"Could not retrieve organization: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@argument("workspace-id")
def get_workspace(config: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
    """Get workspace"""
    api_instance = get_workspace_api_instance(config, keycloak_token)
    try:
        workspace = api_instance.get_workspace(organization_id=organization_id, workspace_id=workspace_id)
        logger.info(f"Workspace retrieved successfully {workspace.id}")
        return CommandResponse.success({workspace.id: workspace.model_dump()})
    except Exception as e:
        logger.error(f"Could not retrieve workspace: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@argument("solution-id")
def get_solution(config: dict, keycloak_token: str, organization_id: str, solution_id: str) -> CommandResponse:
    """Get solution"""
    api_instance = get_solution_api_instance(config, keycloak_token)
    try:
        solution = api_instance.get_solution(organization_id=organization_id, solution_id=solution_id)
        logger.info(f"Solution retrieved successfully {solution.id}")
        return CommandResponse.success({solution.id: solution.model_dump()})
    except Exception as e:
        logger.error(f"Could not retrieve solution: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@argument("dataset-id")
def get_dataset(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str
) -> CommandResponse:
    """Get dataset"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        dataset = api_instance.get_dataset(
            organization_id=organization_id, workspace_id=workspace_id, dataset_id=dataset_id
        )
        logger.info(f"Dataset retrieved successfully {dataset.id}")
        return CommandResponse.success(dataset.model_dump())
    except Exception as e:
        logger.error(f"Could not retrieve dataset: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@argument("runner-id")
def get_runner(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """Get runner"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        runner = api_instance.get_runner(
            organization_id=organization_id, workspace_id=workspace_id, runner_id=runner_id
        )
        logger.info(f"Runner retrieved successfully {runner.id}")
        return CommandResponse.success(runner.model_dump())
    except Exception as e:
        logger.error(f"Could not retrieve runner: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@argument("payload_file")
def update_organization(config: dict, keycloak_token: str, organization_id: str, payload_file) -> CommandResponse:
    """
    Update organization
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    organization_update_request = OrganizationUpdateRequest.from_dict(payload)
    api_instance = get_organization_api_instance(config, keycloak_token)
    try:
        updated = api_instance.update_organization(
            organization_id=organization_id, organization_update_request=organization_update_request
        )
        logger.info(f"Organization {updated.id} updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"Could not update organization: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@argument("payload_file")
def update_workspace(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, payload_file
) -> CommandResponse:
    """Update workspace"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    workspace_update_request = WorkspaceUpdateRequest.from_dict(payload)
    api_instance = get_workspace_api_instance(config, keycloak_token)
    try:
        updated = api_instance.update_workspace(
            organization_id=organization_id,
            workspace_id=workspace_id,
            workspace_update_request=workspace_update_request,
        )
        logger.info(f"Workspace {updated.id} updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"Could not update workspace: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--solution-id", required=False, default=None, type=str, help="Solution ID")
@argument("payload_file")
def update_solution(
    config: dict, keycloak_token: str, organization_id: str, solution_id: str, payload_file
) -> CommandResponse:
    """Update solution"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    solution_update_request = SolutionUpdateRequest.from_dict(payload)
    api_instance = get_solution_api_instance(config, keycloak_token)
    try:
        updated = api_instance.update_solution(
            organization_id=organization_id,
            solution_id=solution_id,
            solution_update_request=solution_update_request,
        )
        logger.info(f"Solution {updated.id} updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"Could not update solution: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--dataset-id", required=False, default=None, type=str, help="Dataset ID")
@argument("payload_file")
def update_dataset(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, payload_file
) -> CommandResponse:
    """Update dataset"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_update_request = DatasetUpdateRequest.from_dict(payload)
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        updated = api_instance.update_dataset(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_update_request=dataset_update_request,
            files=[part["sourceName"] for part in payload["parts"]],
        )
        logger.info(f"Dataset {updated.id} updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"Could not update dataset: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--runner-id", required=False, default=None, type=str, help="Runner ID")
@argument("payload_file")
def update_runner(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, payload_file
) -> CommandResponse:
    """Update runner"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    runner_update_request = RunnerUpdateRequest.from_dict(payload)
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        updated = api_instance.update_runner(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
            runner_update_request=runner_update_request,
        )
        logger.info(f"Runner {updated.id} updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"Could not update runner: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
def about(config: dict, keycloak_token: str) -> CommandResponse:
    """Get API about information"""
    api_instance = get_meta_api_instance(config, keycloak_token)
    try:
        about_info: AboutInfo = api_instance.about()
        logger.info(f"API About Information: {about_info}")
        return CommandResponse.success(about_info.to_dict())
    except Exception as e:
        logger.error(f"Could not retrieve about information: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--dataset-id", required=False, default=None, type=str, help="Dataset ID")
@argument("payload_file")
def create_dataset_part(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, payload_file
) -> CommandResponse:
    """Create dataset part"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_part_create_request = DatasetPartCreateRequest.from_dict(payload)
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        created = api_instance.create_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_create_request=dataset_part_create_request,
            file=payload["sourceName"],
        )
        logger.info(f"Dataset part {created.id} created successfully")
        return CommandResponse.success(created.model_dump())
    except Exception as e:
        logger.error(f"Could not create dataset part: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--dataset-id", "-did", required=False, default=None, type=str, help="Dataset ID")
def list_dataset_parts(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str
) -> CommandResponse:
    """List dataset parts"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        dataset_parts = api_instance.list_dataset_parts(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
        )
        logger.info(f"Dataset parts retrieved successfully {[part.id for part in dataset_parts]}")
        return CommandResponse.success({dp.id: dp.model_dump() for dp in dataset_parts})
    except Exception as e:
        logger.error(f"Could not list dataset parts: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--dataset-id", required=False, default=None, type=str, help="Dataset ID")
@argument("dataset_part_id")
def get_dataset_part(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, dataset_part_id: str
) -> CommandResponse:
    """Get dataset part"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        dataset_part = api_instance.get_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
        )
        logger.info(f"Dataset part retrieved successfully {dataset_part.id}")
        return CommandResponse.success(dataset_part.model_dump())
    except Exception as e:
        logger.error(f"Could not retrieve dataset part: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--dataset-id", required=False, default=None, type=str, help="Dataset ID")
@argument("dataset_part_id")
def delete_dataset_part(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, dataset_part_id: str
) -> CommandResponse:
    """Delete dataset part"""
    api_instance = get_dataset_api_instance(config, keycloak_token)
    try:
        api_instance.delete_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
        )
        logger.info("Dataset part deleted successfully")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"Could not delete dataset part: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--dataset-id", required=False, default=None, type=str, help="Dataset ID")
@argument("dataset_part_id")
@argument("payload_file")
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
        updated = api_instance.update_dataset_part(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_part_id=dataset_part_id,
            dataset_part_update_request=dataset_part_update_request,
        )
        logger.info(f"Dataset part {updated.id} updated successfully")
        return CommandResponse.success(updated.model_dump())
    except Exception as e:
        logger.error(f"Could not update dataset part: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--dataset-id", required=False, default=None, type=str, help="Dataset ID")
@option("--dataset-part-id", required=False, default=None, type=str, help="Dataset Part ID")
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
        logger.info(f"Query result: {query_result}")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"Could not query data: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@argument("runner_id")
def start_run(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """Start a run"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        run = api_instance.start_run(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
        )
        logger.info(f"Run {run.id} started successfully")
        return CommandResponse.success(run.model_dump())
    except Exception as e:
        logger.error(f"Could not start run: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@argument("runner_id")
def stop_run(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """Stop a run"""
    api_instance = get_runner_api_instance(config, keycloak_token)
    try:
        api_instance.stop_run(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
        )
        logger.info(f"Run {runner_id} stopped successfully")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"Could not stop run: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--runner-id", required=False, default=None, type=str, help="Runner ID")
@argument("run_id")
def get_run(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, run_id: str
) -> CommandResponse:
    """Get a run"""
    api_instance = get_run_api_instance(config, keycloak_token)
    try:
        run = api_instance.get_run(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
            run_id=run_id,
        )
        logger.info(f"Run {run.id} retrieved successfully")
        return CommandResponse.success(run.model_dump())
    except Exception as e:
        logger.error(f"Could not get run: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--runner-id", required=False, default=None, type=str, help="Runner ID")
@argument("run_id")
def delete_run(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, run_id: str
) -> CommandResponse:
    """Delete a run"""
    api_instance = get_run_api_instance(config, keycloak_token)
    try:
        api_instance.delete_run(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
            run_id=run_id,
        )
        logger.info(f"Run {run_id} deleted successfully")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"Could not delete run: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@argument("runner_id")
def list_runs(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str
) -> CommandResponse:
    """List runs"""
    api_instance = get_run_api_instance(config, keycloak_token)
    try:
        runs = api_instance.list_runs(organization_id=organization_id, workspace_id=workspace_id, runner_id=runner_id)
        logger.info(f"Runs retrieved successfully {[run.id for run in runs]}")
        return CommandResponse.success({run.id: run.model_dump() for run in runs})
    except Exception as e:
        logger.error(f"Could not list runs: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--runner-id", required=False, default=None, type=str, help="Runner ID")
@argument("run_id")
def get_run_logs(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, run_id: str
) -> CommandResponse:
    """Get run logs"""
    api_instance = get_run_api_instance(config, keycloak_token)
    try:
        logs = api_instance.get_run_logs(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
            run_id=run_id,
        )
        logger.info(f"Run logs retrieved successfully {logs}")
        return CommandResponse.success()
    except Exception as e:
        logger.error(f"Could not get run logs: {e}")
        return CommandResponse.fail()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_config
@option("--organization-id", "-oid", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-wid", required=False, default=None, type=str, help="Workspace ID")
@option("--runner-id", required=False, default=None, type=str, help="Runner ID")
@argument("run_id")
def get_run_status(
    config: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, run_id: str
) -> CommandResponse:
    """Get run status"""
    api_instance = get_run_api_instance(config, keycloak_token)
    try:
        status = api_instance.get_run_status(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
            run_id=run_id,
        )
        logger.info(f"Run status retrieved successfully {status}")
        return CommandResponse.success(status.model_dump())
    except Exception as e:
        logger.error(f"Could not get run status: {e}")
        return CommandResponse.fail()
