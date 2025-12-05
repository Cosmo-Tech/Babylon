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
from cosmotech_api.models.dataset_create_request import DatasetCreateRequest
from cosmotech_api.models.organization_create_request import OrganizationCreateRequest
from cosmotech_api.models.runner_create_request import RunnerCreateRequest
from cosmotech_api.models.solution_create_request import SolutionCreateRequest
from cosmotech_api.models.workspace_create_request import WorkspaceCreateRequest
from cosmotech_api.models.organization_update_request import OrganizationUpdateRequest
from cosmotech_api.models.solution_update_request import SolutionUpdateRequest
from cosmotech_api.models.workspace_update_request import WorkspaceUpdateRequest
from cosmotech_api.models.dataset_update_request import DatasetUpdateRequest
from cosmotech_api.models.runner_update_request import RunnerUpdateRequest

from yaml import safe_load

from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


def get_organization_api_instance(state: dict, keycloak_token: str) -> OrganizationApi:
    configuration = Configuration(host=state["services"]["api"]["url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return OrganizationApi(api_client)


def get_solution_api_instance(state: dict, keycloak_token: str) -> SolutionApi:
    configuration = Configuration(host=state["services"]["api"]["url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return SolutionApi(api_client)


def get_workspace_api_instance(state: dict, keycloak_token: str) -> WorkspaceApi:
    configuration = Configuration(host=state["services"]["api"]["url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return WorkspaceApi(api_client)


def get_dataset_api_instance(state: dict, keycloak_token: str) -> DatasetApi:
    configuration = Configuration(host=state["services"]["api"]["url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return DatasetApi(api_client)


def get_runner_api_instance(state: dict, keycloak_token: str) -> RunnerApi:
    configuration = Configuration(host=state["services"]["api"]["url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return RunnerApi(api_client)


def get_run_api_instance(state: dict, keycloak_token: str) -> RunApi:
    configuration = Configuration(host=state["services"]["api"]["url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return RunApi(api_client)


def get_meta_api_instance(state: dict, keycloak_token: str) -> MetaApi:
    configuration = Configuration(host=state["services"]["api"]["url"])
    configuration.access_token = keycloak_token
    api_client = ApiClient(configuration)
    return MetaApi(api_client)


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@argument("payload_file", required=True)
def create_organization(state: dict, keycloak_token: str, payload_file) -> dict:
    """
    Create organization
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    organization_create_request = OrganizationCreateRequest.from_dict(payload)
    api_instance = get_organization_api_instance(state, keycloak_token)
    try:
        created = api_instance.create_organization(organization_create_request)
        logger.info(f"Organization {created.id} created successfully")
    except Exception as e:
        logger.error(f"Could not create organization: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-w", required=False, default=None, type=str, help="Workspace ID")
@argument("payload_file", required=True)
def create_dataset(state: dict, keycloak_token: str, organization_id: str, workspace_id: str, payload_file) -> dict:
    """
    Create dataset
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_create_request = DatasetCreateRequest.from_dict(payload)
    file_contents_list = [part["sourceName"] for part in payload["parts"]]
    api_instance = get_dataset_api_instance(state, keycloak_token)
    try:
        created = api_instance.create_dataset(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_create_request=dataset_create_request,
            files=file_contents_list,
        )
        logger.info(f"Dataset {created.id} created successfully")
    except Exception as e:
        logger.error(f"Could not create dataset: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@argument("payload_file", required=True)
def create_solution(state: dict, keycloak_token: str, organization_id: str, payload_file) -> dict:
    """
    Create solution
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    import json

    solution_create_request = SolutionCreateRequest.from_json(json.dumps(payload))

    api_instance = get_solution_api_instance(state, keycloak_token)
    try:
        created = api_instance.create_solution(organization_id, solution_create_request)
        logger.info(f"Solution {created.id} created successfully")
    except Exception as e:
        logger.error(f"Could not create solution: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--solution-id", required=False, default=None, type=str, help="Solution ID")
@argument("payload_file", required=True)
def create_workspace(state: dict, keycloak_token: str, organization_id: str, solution_id: str, payload_file) -> dict:
    """
    Create workspace
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    payload["solution"]["solutionId"] = solution_id
    workspace_create_request = WorkspaceCreateRequest.from_dict(payload)

    api_instance = get_workspace_api_instance(state, keycloak_token)
    try:
        created = api_instance.create_workspace(organization_id, workspace_create_request)
        logger.info(f"Workspcae {created.id} created successfully")
    except Exception as e:
        logger.error(f"Could not create workspace: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--solution-id", required=False, default=None, type=str, help="Solution ID")
@option("--workspace-id", required=False, default=None, type=str, help="Workspace ID")
@argument("payload_file", required=True)
def create_runner(
    state: dict, keycloak_token: str, organization_id: str, workspace_id: str, solution_id: str, payload_file
) -> dict:
    """
    Create runner
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    payload["solutionId"] = solution_id
    runner_create_request = RunnerCreateRequest.from_dict(payload)

    api_instance = get_runner_api_instance(state, keycloak_token)
    try:
        created = api_instance.create_runner(
            organization_id=organization_id, workspace_id=workspace_id, runner_create_request=runner_create_request
        )
        logger.info(f"Runner {created.id} created successfully")
    except Exception as e:
        logger.error(f"Could not create runner: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@argument("organization_id", required=True, default=False, type=str)
def delete_organization(state: dict, keycloak_token: str, organization_id: str) -> dict:
    """
    Delete organization
    """
    api_instance = get_organization_api_instance(state, keycloak_token)
    try:
        api_instance.delete_organization(organization_id)
        logger.info(f"Organization {organization_id} deleted successfully")
    except Exception as e:
        logger.error(f"Could not delete organization: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
def list_organizations(state: dict, keycloak_token: str) -> dict:
    """
    List organizations
    """
    api_instance = get_organization_api_instance(state, keycloak_token)
    try:
        organizations = api_instance.list_organizations()
        logger.info(f"Organizations retrieved successfully{[org.id for org in organizations]}")
    except Exception as e:
        logger.error(f"Could not list organizations: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@retrieve_state
def list_workspaces(state: dict, keycloak_token: str, organization_id: str) -> dict:
    """
    List workspaces
    """
    api_instance = get_workspace_api_instance(state, keycloak_token)
    try:
        workspaces = api_instance.list_workspaces(organization_id=organization_id)
        logger.info(f"Workspaces retrieved successfully{[workspace.id for workspace in workspaces]}")
    except Exception as e:
        logger.error(f"Could not list workspace: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-w", required=False, default=None, type=str, help="Workspace ID")
@retrieve_state
def list_datasets(state: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> dict:
    """
    List datasets
    """
    api_instance = get_dataset_api_instance(state, keycloak_token)
    try:
        datasets = api_instance.list_datasets(organization_id=organization_id, workspace_id=workspace_id)
        logger.info(f"Datasets retrieved successfully{[dataset.id for dataset in datasets]}")
    except Exception as e:
        logger.error(f"Could not list datasets: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@argument("solution_id", required=True, default=False, type=str)
def delete_solution(state: dict, keycloak_token: str, organization_id: str, solution_id: str) -> dict:
    """Delete solution"""
    api_instance = get_solution_api_instance(state, keycloak_token)
    try:
        api_instance.delete_solution(organization_id=organization_id, solution_id=solution_id)
        logger.info("Solution deleted successfully")
    except Exception as e:
        logger.error(f"Could not delete solution: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@argument("workspace_id", required=True, default=False, type=str)
def delete_workspace(state: dict, keycloak_token: str, organization_id: str, workspace_id: str) -> dict:
    """Delete workspace"""
    api_instance = get_workspace_api_instance(state, keycloak_token)
    try:
        api_instance.delete_workspace(organization_id=organization_id, workspace_id=workspace_id)
        logger.info("Workspace deleted successfully")
    except Exception as e:
        logger.error(f"Could not delete workspace: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-w", required=False, default=None, type=str, help="Workspace ID")
@argument("runner_id", required=True, default=False, type=str)
def delete_runner(state: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str) -> dict:
    """Delete runner"""
    api_instance = get_runner_api_instance(state, keycloak_token)
    try:
        api_instance.delete_runner(organization_id=organization_id, workspace_id=workspace_id, runner_id=runner_id)
        logger.info("Runner deleted successfully")
    except Exception as e:
        logger.error(f"Could not delete runner: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-w", required=False, default=None, type=str, help="Workspace ID")
@argument("dataset_id", required=True, default=False, type=str)
def delete_dataset(state: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str) -> dict:
    """Delete dataset"""
    api_instance = get_dataset_api_instance(state, keycloak_token)
    try:
        api_instance.delete_dataset(organization_id=organization_id, workspace_id=workspace_id, dataset_id=dataset_id)
        logger.info("Dataset deleted successfully")
    except Exception as e:
        logger.error(f"Could not delete dataset: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@retrieve_state
def list_solutions(state: dict, keycloak_token: str, organization_id: str):
    """List solutions"""
    api_instance = get_solution_api_instance(state, keycloak_token)
    try:
        solutions = api_instance.list_solutions(organization_id=organization_id)
        logger.info(f"Solutions retrieved successfully{[solution.id for solution in solutions]}")
    except Exception as e:
        logger.error(f"Could not list solutions: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-w", required=False, default=None, type=str, help="Workspace ID")
@retrieve_state
def list_runners(state: dict, keycloak_token: str, organization_id: str, workspace_id: str):
    """List runners"""
    api_instance = get_runner_api_instance(state, keycloak_token)
    try:
        runners = api_instance.list_runners(organization_id=organization_id, workspace_id=workspace_id)
        logger.info(f"Runners retrieved successfully{[runner.id for runner in runners]}")
    except Exception as e:
        logger.error(f"Could not list runners: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@argument("organization-id", type=str)
def get_organization(state: dict, keycloak_token: str, organization_id: str):
    """Get organization"""
    api_instance = get_organization_api_instance(state, keycloak_token)
    try:
        organization = api_instance.get_organization(organization_id=organization_id)
        logger.info(f"Organization retrieved successfully{organization.id}")
    except Exception as e:
        logger.error(f"Could not retrieve organization: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@argument("workspace-id", type=str)
def get_workspace(state: dict, keycloak_token: str, organization_id: str, workspace_id: str):
    """Get workspace"""
    api_instance = get_workspace_api_instance(state, keycloak_token)
    try:
        workspace = api_instance.get_workspace(organization_id=organization_id, workspace_id=workspace_id)
        logger.info(f"Workspace retrieved successfully{workspace.id}")
    except Exception as e:
        logger.error(f"Could not retrieve workspace: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@argument("solution-id", type=str)
def get_solution(state: dict, keycloak_token: str, organization_id: str, solution_id: str):
    """Get solution"""
    api_instance = get_solution_api_instance(state, keycloak_token)
    try:
        solution = api_instance.get_solution(organization_id=organization_id, solution_id=solution_id)
        logger.info(f"Solution retrieved successfully{solution.id}")
    except Exception as e:
        logger.error(f"Could not retrieve solution: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-w", required=False, default=None, type=str, help="Workspace ID")
@argument("dataset-id", required=False, type=str)
def get_dataset(state: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str):
    """Get dataset"""
    api_instance = get_dataset_api_instance(state, keycloak_token)
    try:
        dataset = api_instance.get_dataset(
            organization_id=organization_id, workspace_id=workspace_id, dataset_id=dataset_id
        )
        logger.info(f"Dataset retrieved successfully{dataset.id}")
    except Exception as e:
        logger.error(f"Could not retrieve dataset: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-w", required=False, default=None, type=str, help="Workspace ID")
@argument("runner-id", type=str)
def get_runner(state: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str):
    """Get runner"""
    api_instance = get_runner_api_instance(state, keycloak_token)
    try:
        runner = api_instance.get_runner(
            organization_id=organization_id, workspace_id=workspace_id, runner_id=runner_id
        )
        logger.info(f"Runner retrieved successfully{runner.id}")
    except Exception as e:
        logger.error(f"Could not retrieve runner: {e}")


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@argument("payload_file", required=True)
def update_organization(state: dict, keycloak_token: str, organization_id: str, payload_file) -> dict:
    """
    Update organization
    """
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    organization_update_request = OrganizationUpdateRequest.from_dict(payload)
    api_instance = get_organization_api_instance(state, keycloak_token)
    try:
        updated = api_instance.update_organization(
            organization_id=organization_id, organization_update_request=organization_update_request
        )
        logger.info(f"Organization {updated.id} updated successfully")
    except Exception as e:
        logger.error(f"Could not update organization: {e}")

@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-w", required=False, default=None, type=str, help="Workspace ID")
@argument("payload_file", required=True)
def update_workspace(state: dict, keycloak_token: str, organization_id: str, workspace_id: str, payload_file) -> dict:
    """Update workspace"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    workspace_update_request = WorkspaceUpdateRequest.from_dict(payload)
    api_instance = get_workspace_api_instance(state, keycloak_token)
    try:
        updated = api_instance.update_workspace(
            organization_id=organization_id,
            workspace_id=workspace_id,
            workspace_update_request=workspace_update_request,
        )
        logger.info(f"Workspace {updated.id} updated successfully")
    except Exception as e:
        logger.error(f"Could not update workspace: {e}")

@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--solution-id", required=False, default=None, type=str, help="Solution ID")
@argument("payload_file", required=True)
def update_solution(state: dict, keycloak_token: str, organization_id: str, solution_id: str, payload_file) -> dict:
    """Update solution"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    solution_update_request = SolutionUpdateRequest.from_dict(payload)
    api_instance = get_solution_api_instance(state, keycloak_token)
    try:
        updated = api_instance.update_solution(
            organization_id=organization_id,
            solution_id=solution_id,
            solution_update_request=solution_update_request,
        )
        logger.info(f"Solution {updated.id} updated successfully")
    except Exception as e:
        logger.error(f"Could not update solution: {e}")

@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-w", required=False, default=None, type=str, help="Workspace ID")
@option("--dataset-id", required=False, default=None, type=str, help="Dataset ID")
@argument("payload_file", required=True)
def update_dataset(state: dict, keycloak_token: str, organization_id: str, workspace_id: str, dataset_id: str, payload_file) -> dict:
    """Update dataset"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    dataset_update_request = DatasetUpdateRequest.from_dict(payload)
    api_instance = get_dataset_api_instance(state, keycloak_token)
    try:
        updated = api_instance.update_dataset(
            organization_id=organization_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            dataset_update_request=dataset_update_request,
            files=[part["sourceName"] for part in payload["parts"]]
        )
        logger.info(f"Dataset {updated.id} updated successfully")
    except Exception as e:
        logger.error(f"Could not update dataset: {e}")

@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "-o", required=False, default=None, type=str, help="Organization ID")
@option("--workspace-id", "-w", required=False, default=None, type=str, help="Workspace ID")
@option("--runner-id", required=False, default=None, type=str, help="Runner ID")
@argument("payload_file", required=True)
def update_runner(state: dict, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, payload_file) -> dict:
    """Update runner"""
    with open(payload_file, "r") as f:
        payload = safe_load(f)
    runner_update_request = RunnerUpdateRequest.from_dict(payload)
    api_instance = get_runner_api_instance(state, keycloak_token)
    try:
        updated = api_instance.update_runner(
            organization_id=organization_id,
            workspace_id=workspace_id,
            runner_id=runner_id,
            runner_update_request=runner_update_request,
        )
        logger.info(f"Runner {updated.id} updated successfully")
    except Exception as e:
        logger.error(f"Could not update runner: {e}")