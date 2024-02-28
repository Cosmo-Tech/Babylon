from logging import getLogger

from azure.mgmt.resource import ResourceManagementClient
from click import command
from typing import Any
import json
from azure.mgmt.kusto import KustoManagementClient

from Babylon.commands.azure.arm.service.api import ArmService
from Babylon.commands.azure.func.service.api import AzureAppFunctionService
from Babylon.commands.azure.staticwebapp.service.api import AzureSWAService
from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.commands.azure.adx.database.service.api import AdxDatabaseService
from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.commands.api.workspaces.service.api import WorkspaceService
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import (
    pass_azure_token,
    get_powerbi_token,
    get_azure_credentials,
)
from Babylon.utils.decorators import injectcontext, retrieve_state, timing_decorator
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_azure_token("csm_api")
@retrieve_state
def destroy(state: dict, azure_token: str):
    """Macro Destroy"""
    service_state = state["services"]

    scenario_service = ScenarioService(state=service_state, azure_token=azure_token)
    workspace_service = WorkspaceService(state=service_state, azure_token=azure_token)
    solution_service = SolutionService(state=service_state, azure_token=azure_token)
    # deleting scenarios
    response = scenario_service.get_all()
    scenario_json = response.json()
    scenario_str = json.dumps(scenario_json)
    scenarios = json.loads(scenario_str)
    if scenarios:
        for s in scenarios:
            logger.info(f"Deleting scenario {s.get('id')}....")
            scenario_service.delete(force_validation=True)
    service_state["api"]["scenario_id"] = ""
    # deleting datasets
    workspace_id = service_state["api"]["workspace_id"]
    response = workspace_service.get()
    workspace_json = response.json()
    # workspace_str = json.dumps(workspace_json)
    # workspace = json.loads(workspace_str)
    datasets = workspace_json.get("linkedDatasetIdList", [])
    if datasets:
        for dataset_id in datasets:
            logger.info(f"Deleting dataset {dataset_id}....")
            logger.info(f"Deleting dataset blob {dataset_id}....")
            dataset_service = DatasetService(service_state, azure_token)
            response = dataset_service.get()
            dataset = response.json()
            dataset_name = dataset.get("name").replace(" ", "_").lower()
            blob = env.blob_client.get_blob_client(
                container=service_state["api"]["organization_id"],
                blob=f"{workspace_id}/{dataset_name}",
            )
            if blob.exists():
                blob.delete_blob()
            dataset_service.delete(force_validation=True)

    # webapp_id = service_state["webapp"]["object_id"]
    # logger.info(f"Deleting webapp {webapp_id} ....")
    # swa_svc = AzureSWAService(azure_token=azure_token, state=service_state)
    # swa_svc.delete(webapp_name=webapp_id, force_validation=True)
    # service_state["app"]["object_id"] = ""

    # deleting azure function
    azure_credential = get_azure_credentials()
    subscription_id = state["services"]["azure"]["subscription_id"]
    arm_client = ResourceManagementClient(credential=azure_credential, subscription_id=subscription_id)
    azure_func_service = AzureAppFunctionService(arm_client=arm_client, state=service_state)
    azure_func_service.delete()

    # deleting workspace
    logger.info(f"Deleting workspace {workspace_id} ....")
    workspace_service.delete(force_validation=True)
    service_state["api"]["workspace_id"] = ""

    # EventHub
    arm_service = ArmService(arm_client=arm_client, state=service_state)
    arm_service.delete_event_hub()

    # deleting adx database
    adx_name = service_state["adx"]["database_name"]
    logger.info(f"Deleting ADX workspace cluster {adx_name} ....")
    kusto_client = KustoManagementClient(credential=azure_credential, subscription_id=subscription_id)
    adx_svc = AdxDatabaseService(kusto_client=kusto_client, state=service_state)
    adx_svc.delete(name=adx_name)

    # deleting powerBI workspace
    powerbi_workspace_id = service_state["powerbi"]["workspace.id"]
    logger.info(f"Deleting PowerBI workspace {powerbi_workspace_id} ....")
    pb_token = get_powerbi_token()
    powerbi_svc = AzurePowerBIWorkspaceService(powerbi_token=pb_token, state=service_state)
    powerbi_svc.delete(workspace_id=powerbi_workspace_id, force_validation=True)
    service_state["powerbi"]["workspace.id"] = ""

    solution_id = service_state["api"]["solution_id"]
    logger.info(f"Deleting solution {solution_id} ....")
    solution_service.delete(force_validation=True)

    logger.info(f"Deleting run templates for solution {solution_id} ....")
    blob = env.blob_client.get_blob_client(container=service_state["api"]["organization_id"], blob=f"{solution_id}")
    if blob.exists():
        blob.delete_blob()
    service_state["api"]["solution_id"] = ""

    state["services"] = service_state
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)

    return CommandResponse.success()
