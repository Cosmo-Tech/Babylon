from logging import getLogger
from click import command
from typing import Any
import json
from Babylon.services.organizations_service import OrganizationService
from Babylon.commands.api.connectors.service.api import ConnectorService
from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.commands.api.workspaces.service.api import WorkspaceService
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse
from Babylon.services.blob import blob_client
from Babylon.commands.azure.storage.container.service.api import (
    AzureStorageContainerService,
)

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_azure_token("csm_api")
@retrieve_state
def destroy(state: Any, azure_token: str):
    """Macro Destroy"""
    api_state = state["services"]["api"]

    account_secret = env.get_platform_secret(
        platform=env.environ_id, resource="storage", name="account"
    )
    storage_name = state["services"]["azure"]["storage_account_name"]
    blob = blob_client(storage_name=storage_name, account_secret=account_secret, container=api_state["organization_id"])
    azure_service = AzureStorageContainerService(state=state, blob_client=blob)

    scenario_service = ScenarioService(state, azure_token)
    workspace_service = WorkspaceService(state, azure_token)
    solution_service = SolutionService(state, azure_token)

    scenarios_json = scenario_service.get_all()
    scenarios = json.loads(scenarios_json)
    for s in scenarios:
        scenario_service.delete(True)
    api_state["scenario_id"] = ""

    workspace_json = workspace_service.get()
    workspace = json.loads(workspace_json)
    datasets = workspace.get("linkedDatasetIdList")
    for d in datasets:
        state["services"]["api"]["dataset_id"] = d
        azure_service.delete(api_state["dataset_id"])
        dataset_service = DatasetService(state, azure_token)
        dataset_service.delete(True)
    api_state["dataset_id"] = ""

    # webapp
    # webapp
    # webapp
    # webapp

    workspace_service.delete(True)
    api_state["workspace_id"] = ""

    solution_service.delete(True)
    azure_service.delete(api_state["solution_id"])
    api_state["solution_id"] = ""

    state["services"]["api"] = api_state
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)

    logger(state)

    return CommandResponse.success()
