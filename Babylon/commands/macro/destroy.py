import json
import pathlib

from logging import getLogger
from click import command, option
from azure.mgmt.kusto import KustoManagementClient
from azure.mgmt.resource import ResourceManagementClient
from Babylon.commands.azure.arm.service.api import ArmService
from Babylon.commands.api.datasets.service.api import DatasetService
from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.commands.api.workspaces.service.api import WorkspaceService
from Babylon.commands.azure.func.service.api import AzureAppFunctionService
from Babylon.commands.azure.adx.database.service.api import AdxDatabaseService
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
    if state_to_destroy and state_to_destroy.exists():
        data = state_to_destroy.open().read()
        state_to_destroy_json = yaml_to_json(data)
        state_to_destroy_dict = json.loads(state_to_destroy_json)
        service_state = state_to_destroy_dict.get("services")
    else:
        service_state = state["services"]

    if service_state is None:
        logger.error("No state found to execute destroy command")

    workspace_service = WorkspaceService(state=service_state, azure_token=azure_token)
    solution_service = SolutionService(state=service_state, azure_token=azure_token)

    workspace_id = service_state["api"]["workspace_id"]
    solution_id = service_state["api"]["solution_id"]

    # deleting scenarios
    if workspace_id:
        scenario_service = ScenarioService(state=service_state, azure_token=azure_token)
        response = scenario_service.get_all()
        scenario_json = response.json()
        scenario_str = json.dumps(scenario_json)
        scenarios = json.loads(scenario_str)
        if scenarios:
            for s in scenarios:
                logger.info(f"Deleting scenario {s.get('id')}....")
                scenario_service.delete(force_validation=True)
        state["services"]["api"]["scenario_id"] = ""
        env.store_state_in_local(state=state)
        env.store_state_in_cloud(state=state)

    # deleting datasets
    if workspace_id:
        response = workspace_service.get()
        workspace_json = response.json()
        datasets = workspace_json.get("linkedDatasetIdList", [])
        if datasets:
            for dataset_id in datasets:
                dataset_service = DatasetService(state=service_state, azure_token=azure_token)
                response = dataset_service.get(dataset_id=dataset_id)
                dataset = response.json()
                if dataset["sourceType"] == "AzureStorage":
                    dataset_name = dataset.get("name").replace(" ", "_").lower()
                    blob = env.blob_client.get_blob_client(
                        container=service_state["api"]["organization_id"],
                        blob=f"{workspace_id}/{dataset_name}",
                    )
                    if blob.exists():
                        logger.info(f"Deleting dataset blob {dataset_id}....")
                        blob.delete_blob()
                logger.info(f"Deleting dataset {dataset_id}....")
                dataset_service.delete(dataset_id=dataset_id, force_validation=True)

    # # deleting web app
    # webapp_id = "babylouTestdestroy4"
    # logger.info(f"Deleting webapp {webapp_id} ....")
    # azure_token = get_azure_token()
    # subscription_id = service_state["azure"]["subscription_id"]
    #
    # swa_svc = AzureSWAService(
    #     azure_token=azure_token, state=service_state
    # )
    # swa_svc.delete(webapp_name=webapp_id, force_validation=True)
    # service_state["app"]["object_id"] = ""

    # deleting azure function
    azure_credential = get_azure_credentials()
    subscription_id = state["services"]["azure"]["subscription_id"]
    arm_client = ResourceManagementClient(credential=azure_credential, subscription_id=subscription_id)
    azure_func_service = AzureAppFunctionService(arm_client=arm_client, state=service_state)
    logger.info("Deleting azure function....")
    azure_func_service.delete()

    # deleting EventHub
    arm_service = ArmService(arm_client=arm_client, state=service_state)
    logger.info("Deleting event hub....")
    arm_service.delete_event_hub()

    # deleting adx database
    adx_name = service_state["adx"]["database_name"]
    kusto_client = KustoManagementClient(credential=azure_credential, subscription_id=subscription_id)
    adx_svc = AdxDatabaseService(kusto_client=kusto_client, state=service_state)
    logger.info(f"Deleting ADX workspace cluster {adx_name} ....")
    adx_svc.delete(name=adx_name)

    # # deleting powerBI workspace
    powerbi_workspace_id = service_state["powerbi"]["workspace.id"]
    pb_token = get_powerbi_token()
    powerbi_svc = AzurePowerBIWorkspaceService(powerbi_token=pb_token, state=service_state)
    logger.info(f"Deleting PowerBI workspace {powerbi_workspace_id} ....")
    powerbi_svc.delete(workspace_id=powerbi_workspace_id, force_validation=True)
    state["services"]["powerbi"]["workspace.id"] = ""
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)

    # deleting workspace
    if workspace_id:
        logger.info(f"Deleting workspace {workspace_id} ....")
        workspace_service.delete(force_validation=True)
        state["services"]["api"]["workspace_id"] = ""
        env.store_state_in_local(state=state)
        env.store_state_in_cloud(state=state)

    # deleting run templates
    if solution_id:
        solution = solution_service.get()
        solution_json = solution.json()
        run_templates = solution_json.get("runTemplates", [])
        for run_template in run_templates:
            if run_template["preRun"]:
                blob = env.blob_client.get_blob_client(container=service_state["api"]["organization_id"],
                                                       blob=f"{solution_id}"
                                                       f"/{run_template['id']}/prerun.zip")
                if blob.exists():
                    logger.info(f"Deleting run template {run_template['id']} - preRun handler....")
                    blob.delete_blob()
            if run_template["postRun"]:
                blob = env.blob_client.get_blob_client(container=service_state["api"]["organization_id"],
                                                       blob=f"{solution_id}/"
                                                       f"{run_template['id']}/postrun.zip")
                if blob.exists():
                    logger.info(f"Deleting run template {run_template['id']} - postRun handler....")
                    blob.delete_blob()
            if run_template["run"]:
                blob = env.blob_client.get_blob_client(container=service_state["api"]["organization_id"],
                                                       blob=f"{solution_id}/"
                                                       f"{run_template['id']}/run.zip")
                if blob.exists():
                    logger.info(f"Deleting run template {run_template['id']} - run handler....")
                    blob.delete_blob()

        # deleting solution
        if solution_id:
            logger.info(f"Deleting solution {solution_id} ....")
            solution_service.delete(force_validation=True)
            state["services"]["api"]["solution_id"] = ""
            env.store_state_in_local(state=state)
            env.store_state_in_cloud(state=state)

    return CommandResponse.success()
