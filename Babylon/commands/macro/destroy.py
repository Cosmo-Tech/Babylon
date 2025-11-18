import click
import json
import pathlib

from logging import getLogger
from click import command, option
from azure.mgmt.resource import ResourceManagementClient
from Babylon.commands.azure.arm.services.arm_api_svc import ArmService
from Babylon.commands.api.datasets.services.datasets_api_svc import DatasetService
from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.commands.powerbi.workspace.services.powerbi_workspace_api_svc import AzurePowerBIWorkspaceService
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import (
    pass_azure_token,
    get_powerbi_token,
    get_azure_credentials,
)
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse
from Babylon.utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_azure_token("csm_api")
@retrieve_state
@option("--state-to-destroy", "state_to_destroy", type=pathlib.Path)
def destroy(state: dict, azure_token: str, state_to_destroy: pathlib.Path):
    """Macro Destroy"""
    if state_to_destroy and state_to_destroy.exists():
        data = state_to_destroy.open().read()
        state_to_destroy_json = yaml_to_json(data)
        state_to_destroy_dict = json.loads(state_to_destroy_json)
        state = state_to_destroy_dict

    organization_id = state['services']["api"]["organization_id"]
    workspace_id = state['services']["api"]["workspace_id"]
    solution_id = state['services']["api"]["solution_id"]
    workspace_service = WorkspaceService(state=state.get('services'), azure_token=azure_token)
    solution_service = SolutionService(state=state.get('services'), azure_token=azure_token)
    logger.info(f"Starting deletion of solution deployed in organization : {organization_id}")
    # deleting scenarios
    if workspace_id:
        scenario_service = RunnerService(state=state.get('services'), azure_token=azure_token)
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
                        organization_id,
                        blob=f"{workspace_id}/{dataset_name}",
                    )
                    if blob.exists():
                        logger.info(f"Deleting dataset blob {dataset_id}....")
                        blob.delete_blob()
                logger.info(f"Deleting dataset {dataset_id}....")
                dataset_service.delete(dataset_id=dataset_id, force_validation=True)
    env.store_state_in_local(state=state)
    if env.remote:
        env.store_state_in_cloud(state=state)

    # deleting azure function
    azure_credential = get_azure_credentials()
    subscription_id = state["services"]["azure"]["subscription_id"]
    arm_client = ResourceManagementClient(credential=azure_credential, subscription_id=subscription_id)

    # deleting EventHub
    eventhub_key = f"{organization_id} - {state['services']['api']['workspace_key']}"
    arm_service = ArmService(arm_client=arm_client, state=state.get('services'))
    logger.info(f"Deleting event hub : {eventhub_key} ....")
    arm_service.delete_event_hub()
    env.store_state_in_local(state=state)
    if env.remote:
        env.store_state_in_cloud(state=state)

    # # deleting powerBI workspace
    powerbi_workspace_id = state['services']["powerbi"]["workspace.id"]
    if powerbi_workspace_id:
        pb_token = get_powerbi_token()
        powerbi_svc = AzurePowerBIWorkspaceService(powerbi_token=pb_token, state=state.get('services'))
        logger.info(f"Deleting PowerBI workspace {powerbi_workspace_id} ....")
        powerbi_svc.delete(workspace_id=powerbi_workspace_id, force_validation=True)
        state["services"]["powerbi"]["workspace.id"] = ""
        state["services"]["powerbi"]["workspace.name"] = ""
    env.store_state_in_local(state=state)
    if env.remote:
        env.store_state_in_cloud(state=state)

    # deleting workspace
    if workspace_id:
        logger.info(f"Deleting API workspace {workspace_id} ....")
        workspace_service.delete(force_validation=True)
        state["services"]["api"]["workspace_id"] = ""
    env.store_state_in_local(state=state)
    if env.remote:
        env.store_state_in_cloud(state=state)

    # deleting run templates
    if solution_id:
        solution = solution_service.get()
        solution_json = solution.json()
        run_templates = solution_json.get("runTemplates", [])
        handlers = ['parameters_handler', 'preRun', 'run', 'engine', 'postRun', 'scenariodata_transform', 'validator']
        for run_template in run_templates:
            runtemplate_id = run_template.get('id', "")
            for h in handlers:
                blob = env.blob_client.get_blob_client(container=organization_id,
                                                       blob=f"{solution_id}/{runtemplate_id}/{h}.zip")
                if blob.exists():
                    logger.info(f"Deleting run template {h} - {run_template} in solution : {solution_id}")
                    blob.delete_blob()
        # deleting solution
        logger.info(f"Deleting solution {solution_id} ....")
        solution_service.delete(force_validation=True)
        state["services"]["api"]["solution_id"] = ""

    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)
    _ret = ['']
    _ret.append("")
    _ret.append("Deployments: ")
    _ret.append("")
    _ret.append(f"   * Organization   : {state['services'].get('api').get('organization_id', '')}")
    _ret.append(f"   * Solution       : {solution_id} - Deleted")
    _ret.append("      * RunTemplates: All Deleted")
    _ret.append(f"   * Workspace      : {workspace_id} - Deleted")
    _ret.append("      * EvenHub     : Deleted")
    _ret.append("      * Database    : Deleted")
    _ret.append("      * PowerBI     : Deleted")
    _ret.append("   * Datasets       : All Deleted")
    _ret.append("      * Storage     : All Deleted")
    _ret.append("   * Scenarios      : All Deleted")
    _ret.append("   * ScenarioRuns   : All Deleted")
    if state["services"].get('webapp').get('static_domain', ''):
        _ret.append("   * WebApp         ")
        _ret.append(f"      * Hostname    : https://{state['services'].get('webapp').get('static_domain', '')}")
    click.echo(click.style("\n".join(_ret), fg="green"))

    return CommandResponse.success()
