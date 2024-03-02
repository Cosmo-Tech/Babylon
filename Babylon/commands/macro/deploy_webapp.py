import os
import sys
import json
import time
import yaml
import shutil

from pathlib import Path
from logging import getLogger
from Babylon.utils.environment import Environment
from azure.mgmt.resource import ResourceManagementClient
from Babylon.commands.azure.arm.services.api import ArmService
from Babylon.commands.webapp.service.api import AzureWebAppService
from Babylon.commands.git_hub.runs.service.api import GitHubRunsService
from Babylon.commands.azure.staticwebapp.services.api import AzureSWAService
from Babylon.utils.credentials import get_azure_credentials, get_azure_token
from Babylon.commands.azure.staticwebapp.services.app_settings import AzureSWASettingsAppService

logger = getLogger("Babylon")
env = Environment()


def deploy_swa(file_content: str):
    logger.info("webapp deployment")
    platform_url = env.set_ns_from_yaml(content=file_content)
    state = env.retrieve_state_func()
    state['services']['api']['url'] = platform_url
    subscription_id = state["services"]["azure"]["subscription_id"]
    github_secret = env.get_global_secret(resource="github", name="token")
    organization_id = state['services']['api']['organization_id']
    workspace_key = state['services']['api']['workspace_key']
    obi_secret = env.get_project_secret(
        organization_id=organization_id,
        workspace_key=workspace_key,
        name="pbi")
    ext_args = dict(github_secret=github_secret, secret_powerbi=obi_secret)
    content = env.fill_template(data=file_content, state=state, ext_args=ext_args)
    sidecars = content.get("spec").get("sidecars", {})
    payload: dict = content.get("spec").get("payload", {})
    github_section = sidecars.get('github', {})
    if github_section:
        state['services']['github']['organization'] = github_section.get('organization_name', "")
        state['services']['github']['repository'] = github_section.get('repository_name', "")
        state['services']["github"]["branch"] = github_section.get('branch', "")
    # app = sidecars.get('azure').get('app', {})
    # if app:
    #     azure_token = get_azure_token("graph")
    #     app_svc = AzureDirectoyAppService(azure_token=azure_token, state=state.get('services'))
    #     details = json.dumps(obj=app.get('payload'), indent=4, ensure_ascii=True)
    #     object_id = state['services']['app']["object_id"]
    #     get_app = app_svc.get(object_id=object_id)
    #     if not get_app:
    #       app_created, sp = app_svc.create(details=details)
    #       state['services']['app']["client_id"] = app_created["appId"]
    #       state['services']['app']["name"] = app_created["appDisplayName"]
    #       state['services']['app']["principal_id"] = app_created["id"]
    #       state['services']['app']["object_id"] = sp["id"]
    #       env.store_state_in_local(state)
    #       env.store_state_in_cloud(state)
    #       app_secrets = AzureDirectoyPasswordService(azure_token=azure_token, state=state.get('services'))
    #       app_secrets.create(object_id=sp["id"], password_name="pbi")
    #       app_secrets.create(object_id=sp["id"], password_name="azf")
    #       add this app to powerbi group (az)
    #       if group_id:
    #           group_svc = AzureDirectoyMemberService(azure_token=azure_token)
    #           group_svc.add(group_id=group_id, principal_id=app_created["id"])
    #           print("add app ")
    #       else:
    #           app_svc.update(object_id=object_id, details=details)
    swa_name = payload.get('name', "")
    swa = dict()
    if payload:
        azure_token = get_azure_token()
        del payload['name']
        swa_svc = AzureSWAService(azure_token=azure_token, state=state.get('services'))
        swas = swa_svc.get_all(filter="[].name")
        if swa_name not in swas:
            print("webapp not found")
            payload_str = json.dumps(obj=payload, indent=4, ensure_ascii=True)
            swa = swa_svc.create(webapp_name=swa_name, details=payload_str)
            state['services']['webapp']['static_domain'] = swa["properties"]['defaultHostname']
            time.sleep(5)
            github_svc = GitHubRunsService(state=state.get('services'))
            workflow_name = swa["properties"]['defaultHostname'].split(".")[0]
            workflow_github = github_svc.get(workflow_name=workflow_name)
            if workflow_github:
                github_svc.cancel(run_url=workflow_github)
            time.sleep(5)
            webapp_svc = AzureWebAppService(state=state.get('services'))
            webapp_path = Path().cwd() / "webapp_src"
            webapp_svc.download(webapp_path)
            config = yaml.dump(sidecars.get('config', {}))
            c_path = Path().cwd() / "webapp_src/config.json"
            webapp_svc.export_config(data=config, config_path=c_path)
            time.sleep(5)
            workflow_name_full = f"azure-static-web-apps-{workflow_name}.yml"
            workflow_file = Path().cwd() / f"webapp_src/.github/workflows/{workflow_name_full}"
            webapp_svc.update_workflow(workflow_file=workflow_file)
            config_file = Path().cwd() / "webapp_src/config.json"
            webapp_svc.upload_many([workflow_file, config_file])
            time.sleep(5)
            shutil.rmtree(path=webapp_path)
            env.store_state_in_local(state)
            env.store_state_in_cloud(state)
    powerbi = sidecars.get('powerbi', {})
    if powerbi:
        azure_token = get_azure_token()
        swa_settings = AzureSWASettingsAppService(azure_token=azure_token, state=state.get('services'))
        organization_id = state['services']['api']['organization_id']
        workspace_key = state['services']['api']['workspace_key']
        secret_powerbi = env.get_project_secret(organization_id=organization_id,
                                                workspace_key=workspace_key,
                                                name="pbi")
        ext_args = dict(github_secret=github_secret, secret_powerbi=secret_powerbi)
        content = env.fill_template(data=file_content, state=state, ext_args=ext_args)
        powerbi = content.get("spec").get("sidecars").get('powerbi', {})
        settings = powerbi.get('settings')
        settings_str = json.dumps(obj=settings, indent=4, ensure_ascii=True)
        swa_settings.update(webapp_name=swa_name, details=settings_str)
    function_spec = sidecars.get("azure").get("function", {})
    if function_spec:
        url_zip = function_spec.get('url_zip')
        azure_credential = get_azure_credentials()
        arm_client = ResourceManagementClient(credential=azure_credential, subscription_id=subscription_id)
        azf_secret = env.get_project_secret(organization_id=organization_id, workspace_key=workspace_key, name="azf")
        arm_svc = ArmService(arm_client=arm_client, state=state.get('services'))
        ext_args = dict(azure_app_client_secret=azf_secret, url_zip=url_zip)
        arm_svc.run(deployment_name="funcappmyde", file="azf_deploy.json", ext_args=ext_args)
    run_scripts = sidecars.get("run_scripts")
    if run_scripts:
        data = run_scripts.get("post_deploy.sh", "")
        if data:
            os.system(data)
    if not swa.get('id'):
        sys.exit(1)
