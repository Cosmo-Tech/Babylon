<<<<<<< HEAD
=======
from logging import getLogger

from azure.mgmt.resource import ResourceManagementClient
from click import command
from typing import Any
>>>>>>> 420b6228 (feat: [PROD-13024] add delete event hub and azure function)
import json
import pathlib

from logging import getLogger
from click import command, option
from azure.mgmt.kusto import KustoManagementClient
<<<<<<< HEAD
from azure.mgmt.resource import ResourceManagementClient
from Babylon.commands.azure.arm.services.api import ArmService
from Babylon.commands.api.datasets.services.api import DatasetService
from Babylon.commands.api.scenarios.services.api import ScenarioService
from Babylon.commands.api.solutions.services.api import SolutionService
from Babylon.commands.api.workspaces.services.api import WorkspaceService
from Babylon.commands.azure.func.services.api import AzureAppFunctionService
from Babylon.commands.azure.adx.services.database import AdxDatabaseService
=======

from Babylon.commands.azure.arm.service.api import ArmService
from Babylon.commands.azure.func.service.api import AzureAppFunctionService
from Babylon.commands.azure.staticwebapp.service.api import AzureSWAService
from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.commands.azure.adx.database.service.api import AdxDatabaseService
from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.commands.api.workspaces.service.api import WorkspaceService
>>>>>>> 420b6228 (feat: [PROD-13024] add delete event hub and azure function)
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import (
    pass_azure_token,
    get_powerbi_token,
    get_azure_credentials,
)
from Babylon.utils.decorators import injectcontext, retrieve_state, timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_azure_token("csm_api")
@retrieve_state
@option("--state-to-destroy", "state_to_destroy", type=pathlib.Path)
def destroy(state: dict, azure_token: str, state_to_destroy: pathlib.Path):
    """Macro Destroy"""
<<<<<<< HEAD
    if state_to_destroy and state_to_destroy.exists():
        data = state_to_destroy.open().read()
        state_to_destroy_json = yaml_to_json(data)
        state_to_destroy_dict = json.loads(state_to_destroy_json)
        state = state_to_destroy_dict
    workspace_id = state['services']["api"]["workspace_id"]
    solution_id = state['services']["api"]["solution_id"]
    workspace_service = WorkspaceService(state=state.get('services'), azure_token=azure_token)
    solution_service = SolutionService(state=state.get('services'), azure_token=azure_token)
    # deleting scenarios
    if workspace_id:
        scenario_service = ScenarioService(state=state.get('services'), azure_token=azure_token)
        response = scenario_service.get_all()
        scenario_json = response.json()
        scenario_str = json.dumps(scenario_json)
        scenarios = json.loads(scenario_str)
        if scenarios:
            for s in scenarios:
                logger.info(f"Deleting scenario {s.get('id')}....")
                scenario_service.delete(force_validation=True)
        state["services"]["api"]["scenario_id"] = ""
    # deleting datasets
    if workspace_id:
        response = workspace_service.get()
        workspace_json = response.json()
        datasets = workspace_json.get("linkedDatasetIdList", [])
        if datasets:
            for dataset_id in datasets:
                dataset_service = DatasetService(state=state['services'], azure_token=azure_token)
                response = dataset_service.get(dataset_id=dataset_id)
                dataset = response.json()
                if dataset["sourceType"] == "AzureStorage":
                    dataset_name = dataset.get("name").replace(" ", "_").lower()
                    blob = env.blob_client.get_blob_client(
                        container=state['services']["api"]["organization_id"],
                        blob=f"{workspace_id}/{dataset_name}",
                    )
                    if blob.exists():
                        logger.info(f"Deleting dataset blob {dataset_id}....")
                        blob.delete_blob()
                logger.info(f"Deleting dataset {dataset_id}....")
                dataset_service.delete(dataset_id=dataset_id, force_validation=True)
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)

    # deleting azure function
    azure_credential = get_azure_credentials()
    subscription_id = state["services"]["azure"]["subscription_id"]
    arm_client = ResourceManagementClient(credential=azure_credential, subscription_id=subscription_id)
    azure_func_service = AzureAppFunctionService(arm_client=arm_client, state=state.get('services'))
    logger.info("Deleting azure function....")
    azure_func_service.delete()
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)

    # deleting EventHub
    arm_service = ArmService(arm_client=arm_client, state=state.get('services'))
    logger.info("Deleting event hub....")
    arm_service.delete_event_hub()
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)

    # deleting adx database
    adx_name = state['services']["adx"]["database_name"]
    kusto_client = KustoManagementClient(credential=azure_credential, subscription_id=subscription_id)
    adx_svc = AdxDatabaseService(kusto_client=kusto_client, state=state.get('services'))
    logger.info(f"Deleting ADX workspace cluster {adx_name} ....")
    adx_svc.delete(name=adx_name)
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)

    # # deleting powerBI workspace
    powerbi_workspace_id = state['services']["powerbi"]["workspace.id"]
    if powerbi_workspace_id:
        pb_token = get_powerbi_token()
        powerbi_svc = AzurePowerBIWorkspaceService(powerbi_token=pb_token, state=state.get('services'))
        logger.info(f"Deleting PowerBI workspace {powerbi_workspace_id} ....")
        powerbi_svc.delete(workspace_id=powerbi_workspace_id, force_validation=True)
        state["services"]["powerbi"]["workspace.id"] = ""
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)

    # deleting workspace
    if workspace_id:
        logger.info(f"Deleting API workspace {workspace_id} ....")
        workspace_service.delete(force_validation=True)
        state["services"]["api"]["workspace_id"] = ""
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)

    # deleting run templates
    if solution_id:
        solution = solution_service.get()
        solution_json = solution.json()
        run_templates = solution_json.get("runTemplates", [])
        organization_id = state['services']["api"]["organization_id"]
        handlers = ['parameters_handler', 'preRun', 'run', 'engine', 'postRun', 'scenariodata_transform', 'validator']
        for run_template in run_templates:
            runtemplate_id = run_template.get('id', "")
            for h in handlers:
                blob = env.blob_client.get_blob_client(container=organization_id,
                                                       blob=f"{solution_id}/{runtemplate_id}/{h}.zip")
                if blob.exists():
                    blob.delete_blob()
        # deleting solution
        logger.info(f"Deleting solution {solution_id} ....")
        solution_service.delete(force_validation=True)
        state["services"]["api"]["solution_id"] = ""
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)
=======
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

>>>>>>> 420b6228 (feat: [PROD-13024] add delete event hub and azure function)
    return CommandResponse.success()
