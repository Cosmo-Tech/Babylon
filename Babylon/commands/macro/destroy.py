from logging import getLogger
from click import command
from typing import Any
import json
from azure.mgmt.kusto import KustoManagementClient
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

    response = scenario_service.get_all()
    scenario_json = response.json()
    scenario_str = json.dumps(scenario_json)
    scenarios = json.loads(scenario_str)
    logger.warn(scenarios)
    if scenarios:
        for s in scenarios:
            logger.info(f"Deleting scenario {s['id']}....")
            scenario_service.delete(True)
    service_state["api"]["scenario_id"] = ""

    response = workspace_service.get()
    workspace_json = response.json()
    workspace_str = json.dumps(workspace_json)
    workspace = json.loads(workspace_str)
    datasets = workspace.get("linkedDatasetIdList")
    logger.warn(datasets)

    if datasets.len() > 0:
        for d in datasets:
            logger.info(f"Deleting dataset {d.get('id')}....")
            service_state["api"]["dataset_id"] = d

            logger.info(f"Deleting dataset blob {d.get('d')}....")
            client = env.blob_client.get_blob_client(
                container=service_state["api"]["organization_id"],
                blob=f"{service_state['api']['dataset_id']}",
            )
            client.delete_blob()
            dataset_service = DatasetService(service_state, azure_token)
            dataset_service.delete(True)
    service_state["api"]["dataset_id"] = ""

    webapp_id = service_state["app"]["object_id"]
    logger.info(f"Deleting webapp {webapp_id} ....")
    # Delete azure function

    swa_svc = AzureSWAService(azure_token=azure_token, state=service_state)
    swa_svc.delete(webapp_name=webapp_id, force_validation=True)
    service_state["app"]["object_id"] = ""

    workspace_id = service_state["api"]["workspace_id"]
    logger.info(f"Deleting workspace {workspace_id} ....")
    workspace_service.delete(True)
    # EventHub

    adx_name = f"{state['services']['api']['organization_id']}-{state['services']['api']['workspace_key']}"
    logger.info(f"Deleting ADX workspace cluster {adx_name} ....")
    azure_credential = get_azure_credentials()
    subscription_id = service_state["azure"]["subscription_id"]
    kusto_client = KustoManagementClient(
        credential=azure_credential, subscription_id=subscription_id
    )
    adx_svc = AdxDatabaseService(kusto_client=kusto_client, state=  service_state)
    adx_svc.delete(name=adx_name)

    logger.info(f"Deleting PowerBI workspace {workspace_id} ....")
    pb_token = get_powerbi_token()
    powerbi_svc = AzurePowerBIWorkspaceService(
        powerbi_token=pb_token, state=service_state
    )
    powerbi_svc.delete(workspace_id=workspace_id, force_validation=True)
    service_state["api"]["workspace_id"] = ""

    solution_id = service_state["api"]["solution_id"]
    logger.info(f"Deleting solution {solution_id} ....")
    solution_service.delete(True)

    logger.info(f"Deleting solution blob {solution_id} ....")
    client = env.blob_client.get_blob_client(
        container=service_state["api"]["organization_id"], blob=f"{solution_id}"
    )
    client.delete_blob()
    service_state["api"]["solution_id"] = ""

    state["services"] = service_state
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)

    logger(state)

    return CommandResponse.success()
