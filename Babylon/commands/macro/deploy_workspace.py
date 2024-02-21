# import os
# import json
import pathlib

# from zipfile import ZipFile
from logging import getLogger
# from Babylon.commands.azure.adx.database.service.api import AdxDatabaseService
# from Babylon.commands.azure.arm.service.api import ArmService
# from azure.mgmt.resource import ResourceManagementClient
# from azure.mgmt.kusto import KustoManagementClient
# from Babylon.utils.credentials import get_azure_credentials
# from posixpath import basename
# from Babylon.commands.api.workspaces.service.api import WorkspaceService
from Babylon.utils.environment import Environment
# from Babylon.utils.credentials import get_azure_token
# from Babylon.commands.api.solutions.service.api import SolutionService
# from Babylon.commands.api.solutions.handler.service.api import SolutionHandleService

logger = getLogger("Babylon")
env = Environment()


def deploy_workspace(file_content: dict, deploy_dir: pathlib.Path) -> bool:
    print("Workspace deployment")
    # payload: dict = file_content.get("spec").get("payload")
    # azure_token = get_azure_token("csm_api")
    state = env.retrieve_state_func()
    print(state)
    # service_state = state["services"]
    # service_state["api"]["organization_id"] = "o-2v54kow7wvz6"
    # spec = dict()
    # spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    # workspace_svc = WorkspaceService(
    #     azure_token=azure_token, spec=spec, state=service_state
    # )
    # if not service_state["api"]["solution_id"]:
    #     response = workspace_svc.create()
    #     solution = response.json()
    # else:
    #     response = workspace_svc.update()
    #     response_json = response.json()
    #     old_security = response_json.get("security")
    #     security_spec = workspace_svc.update_security(old_security=old_security)
    #     response_json["security"] = security_spec
    #     solution = response_json
    #     logger.info(solution)
    # env.store_state_in_local(state)
    # env.store_state_in_cloud(state)

    # update run_templates
    # sidecars = file_content.get("spec")["sidecars"]
    # eventhub_section = sidecars["azure"]["eventhub"]
    # subscription_id = state["services"]["azure"]["subscription_id"]
    # azure_credential = get_azure_credentials()
    # if eventhub_section:
    #     arm_client = ResourceManagementClient(credential=azure_credential, subscription_id=subscription_id)
    #     adx_svc = ArmService(arm_client=arm_client, state=state['services'])
    #     adx_svc.run(deployment_name="eventhubtestniabldo")
    # adx_section = sidecars["azure"]["adx"]
    # if adx_section:
    #     kusto_client = KustoManagementClient(credential=azure_credential, subscription_id=subscription_id)
    #     eventhub_svc = AdxDatabaseService(kusto_client=kusto_client, state=state["services"])
    #     state['services']['api']['organization_id'] = "o-2v54kow7wvz6"
    #     state['services']['api']['workspace_key'] = "w-test" 
    #     name = f"{state['services']['api']['organization_id']}-{state['services']['api']['workspace_key']}"
    #     eventhub_svc.create(name=name, retention=365)
    #     consumers_name = eventhub.get('consumers').get('name', "adx")
    return True
