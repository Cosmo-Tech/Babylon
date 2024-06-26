import os
import json
import time
import click
import yaml
import shutil

from pathlib import Path
from logging import getLogger
from Babylon.utils.environment import Environment
from azure.mgmt.resource import ResourceManagementClient
from Babylon.commands.azure.arm.services.arm_api_svc import ArmService
from Babylon.commands.webapp.service.webapp_api_svc import AzureWebAppService
from Babylon.commands.git_hub.runs.service.github_api_svc import GitHubRunsService
from Babylon.commands.azure.ad.services.ad_app_svc import AzureDirectoyAppService
from Babylon.utils.credentials import get_azure_credentials, get_azure_token
from Babylon.commands.azure.staticwebapp.services.swa_api_svc import AzureSWAService
from Babylon.commands.azure.ad.services.ad_member_svc import AzureDirectoyMemberService
from Babylon.commands.azure.ad.services.ad_password_svc import AzureDirectoyPasswordService
from Babylon.commands.azure.staticwebapp.services.swa_app_settings_svc import AzureSWASettingsAppService

logger = getLogger("Babylon")
env = Environment()


def deploy_swa(namespace: str, file_content: str):
    _ret = [""]
    _ret.append("Webapp deployment")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    platform_url = env.get_ns_from_text(content=namespace)
    state = env.retrieve_state_func(state_id=env.state_id)
    vars = env.get_variables()
    metadata = env.get_metadata(vars, file_content)
    workspace_key = metadata['selector'].get('workspace_key', "")
    state['services']['api']['url'] = platform_url
    state['services']['azure']['tenant_id'] = env.tenant_id
    state["services"]["api"]["workspace_key"] = workspace_key
    subscription_id = state["services"]["azure"]["subscription_id"]
    github_secret = env.get_global_secret(resource="github", name="token")
    organization_id = state['services']['api']['organization_id']
    obi_secret = env.get_project_secret(organization_id=organization_id, workspace_key=workspace_key, name="pbi")
    ext_args = dict(github_secret=github_secret, secret_powerbi=obi_secret)
    file_content_obj = yaml.safe_load(file_content)
    config = json.dumps(obj=file_content_obj.get("spec").get('sidecars').get('config', {}), indent=4, ensure_ascii=True)
    content = env.fill_template(data=file_content, state=state, ext_args=ext_args)
    sidecars = content.get("spec").get("sidecars", {})
    payload: dict = content.get("spec").get("payload", {})
    github_section = sidecars.get('github', {})
    if github_section:
        state['services']['github']['organization'] = github_section.get('organization_name', "")
        state['services']['github']['repository'] = github_section.get('repository_name', "")
        state['services']["github"]["branch"] = github_section.get('branch', "")
    app_section = sidecars.get('azure').get('app', {})
    azure_token = get_azure_token("graph")
    app_svc = AzureDirectoyAppService(azure_token=azure_token, state=state.get('services'))
    if app_section:
        to_create = app_section.get('create', False)
        if not to_create:
            state['services']['app']['app_id'] = app_section.get('use').get('client_id')
            state['services']['app']["name"] = app_section.get('use').get("displayName")
            env.store_state_in_local(state)
            if env.remote:
                env.store_state_in_cloud(state)
        if to_create:
            details = json.dumps(obj=app_section.get('payload', {}), indent=4, ensure_ascii=True)
            object_id = state['services']['app']["object_id"]
            get_app = app_svc.get(object_id=object_id)
            if not get_app:
                app_created, sp = app_svc.create(details=details)
                state['services']['app']["app_id"] = app_created.get("appId")
                state['services']['app']["name"] = app_created.get("appDisplayName")
                state['services']['app']["principal_id"] = app_created.get("id")
                state['services']['app']["object_id"] = sp.get("id")
                app_secrets = AzureDirectoyPasswordService(azure_token=azure_token, state=state.get('services'))
                app_secrets.create(object_id=sp.get("id", None), password_name="pbi")
                app_secrets.create(object_id=sp.get("id", None), password_name="azf")
                env.store_state_in_local(state)
                if env.remote:
                    env.store_state_in_cloud(state)
            group_id = sidecars.get('powerbi', {}).get('group_id', '')
            add_to_group_powerbi = sidecars.get('azure').get('app', {}).get('add_to_powerbi', False)
            if group_id and add_to_group_powerbi:
                logger.info(f'adding app to group powerbi {group_id}')
                group_svc = AzureDirectoyMemberService(azure_token=azure_token)
                group_svc.add(group_id=group_id, principal_id=state['services']['app']["principal_id"])
    swa_name = payload.get('name', "")
    swa = dict()
    uris = list()
    if payload:
        webapp_path = Path().cwd() / "webapp_src"
        azure_token = get_azure_token()
        del payload['name']
        swa_svc = AzureSWAService(azure_token=azure_token, state=state.get('services'))
        swas = swa_svc.get_all(filter="[].name")
        if len(swas) == 0 or swa_name not in swas:
            print("webapp not found")
            payload_str = json.dumps(obj=payload, indent=4, ensure_ascii=True)
            swa = swa_svc.create(webapp_name=swa_name, details=payload_str)
            state['services']['webapp']['webapp_name'] = swa_name
            state['services']['webapp']['static_domain'] = swa["properties"]['defaultHostname']
            time.sleep(5)
            github_svc = GitHubRunsService(state=state.get('services'))
            workflow_name = swa["properties"]['defaultHostname'].split(".")[0]
            workflow_github = github_svc.get(workflow_name=workflow_name)
            if workflow_github:
                github_svc.cancel(run_url=workflow_github)
            time.sleep(5)
        if state["services"]["webapp"]["static_domain"]:
            swa_url = f"https://{state['services']['webapp']['static_domain']}/sign-in"
            app_section_payload = app_section.get('payload', {})
            if swa_url not in app_section_payload['spa']['redirectUris']:
                app_section_payload['spa']['redirectUris'].append(swa_url)
                details = json.dumps(obj=app_section_payload, indent=4, ensure_ascii=True)
                object_id = state['services']['app']["object_id"]
                app_svc.update(object_id=object_id, details=details)
            uris = app_section_payload['spa']['redirectUris']
        workflow_name = state['services']['webapp']['static_domain'].split(".")[0]
        webapp_svc = AzureWebAppService(state=state.get('services'))
        webapp_svc.download(webapp_path)
        c_path = Path().cwd() / "webapp_src/config.json"
        webapp_svc.export_config(data=config, config_path=c_path)
        time.sleep(5)
        workflow_name_full = f"azure-static-web-apps-{workflow_name}.yml"
        workflow_file = Path().cwd() / f"webapp_src/.github/workflows/{workflow_name_full}"
        if workflow_file.exists():
            webapp_svc.update_workflow(workflow_file=workflow_file)
            config_file = Path().cwd() / "webapp_src/config.json"
            webapp_svc.upload_many([workflow_file, config_file])
            time.sleep(5)
        shutil.rmtree(path=webapp_path)
        env.store_state_in_local(state)
        if env.remote:
            env.store_state_in_cloud(state)
    powerbi = sidecars.get('powerbi', {})
    if powerbi:
        azure_token = get_azure_token()
        swa_settings = AzureSWASettingsAppService(azure_token=azure_token, state=state.get('services'))
        organization_id = state['services']['api']['organization_id']
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
    if function_spec and len(uris):
        url_zip = function_spec.get('url_zip', '')
        azure_credential = get_azure_credentials()
        arm_client = ResourceManagementClient(credential=azure_credential, subscription_id=subscription_id)
        azf_secret = env.get_project_secret(organization_id=organization_id, workspace_key=workspace_key, name="azf")
        arm_svc = ArmService(arm_client=arm_client, state=state.get('services'))
        instance_name = function_spec.get('name', f"{organization_id}-{workspace_key}")
        deployment_name = function_spec.get('name', f"{organization_id}-azf-{workspace_key}")
        ext_args = dict(azure_app_client_secret=azf_secret,
                        url_zip=url_zip,
                        instance_name=instance_name,
                        redirect_uris=uris)
        arm_svc.run(deployment_name=deployment_name, file="azf_deploy.json", ext_args=ext_args)
    run_scripts = sidecars.get("run_scripts")
    if run_scripts:
        data = run_scripts.get("post_deploy.sh", "")
        if data:
            os.system(data)
