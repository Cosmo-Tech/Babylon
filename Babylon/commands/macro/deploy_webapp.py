import sys
import json

from logging import getLogger
from Babylon.utils.environment import Environment
from azure.mgmt.resource import ResourceManagementClient
from Babylon.commands.azure.arm.service.api import ArmService
from Babylon.commands.azure.staticwebapp.service.api import AzureSWAService
from Babylon.utils.credentials import get_azure_credentials, get_azure_token
from Babylon.commands.azure.ad.app.service.api import AzureDirectoyAppService
from Babylon.commands.azure.ad.app.password.service.api import AzureDirectoyPasswordService
from Babylon.commands.azure.staticwebapp.app_settings.service.api import AzureSWASettingsAppService

logger = getLogger("Babylon")
env = Environment()


def deploy_swa(file_content: str):
    logger.info("webapp deployment")
    state = env.retrieve_state_func()
    subscription_id = state["services"]["azure"]["subscription_id"]
    state['services']['app']["client_id"] = ""
    state['services']['app']["appDisplayName"] = ""
    state['services']['app']["appDisplayName"] = ""
    state['services']['app']["principal_id"] = ""
    state['services']['app']["object_id"] = ""
    service_state = state["services"]
    service_state["api"]["organization_id"] = "o-2v54kow7wvz6"
    service_state["api"]["workspace_key"] = "w-test"
    service_state['azure']['tenant_id'] = "tenantid"
    github_secret = env.get_global_secret(resource="github", name="token")
    ext_args = dict(github_secret=github_secret, secret_powerbi="")
    content = env.fill_template(data=file_content, state=state, ext_args=ext_args)
    sidecars = content.get("spec").get("sidecars", {})
    payload: dict = content.get("spec").get("payload", {})
    swa_name = payload.get('name', "")
    swa = dict()
    if payload:
        azure_token = get_azure_token()
        del payload['name']
        swa_svc = AzureSWAService(azure_token=azure_token, state=service_state)
        swas = swa_svc.get_all(filter="[].name")
        if swa_name in swas:
            # s = sidecars.get('run_scripts', {}).items()
            # for i, data print(data)
            payload_str = json.dumps(obj=payload, indent=4, ensure_ascii=True)
            swa = swa_svc.create(webapp_name=swa_name, details=payload_str)
            service_state['webapp']['static_domain'] = "white-island-0e39f3f03.4.azurestaticapps.net"
    app = sidecars.get('azure').get('app', {})
    if app:
        azure_token = get_azure_token("graph")
        app_svc = AzureDirectoyAppService(azure_token=azure_token, state=service_state)
        details = json.dumps(obj=app.get('payload'), indent=4, ensure_ascii=True)
        object_id = state['services']['app']["object_id"]
        get_app = app_svc.get(object_id=object_id)
        if not get_app:
            app_created, sp = app_svc.create(details=details)
            state['services']['app']["client_id"] = app_created["appId"]
            state['services']['app']["appDisplayName"] = app_created["appDisplayName"]
            state['services']['app']["appDisplayName"] = app_created["appDisplayName"]
            state['services']['app']["principal_id"] = app_created["id"]
            state['services']['app']["object_id"] = sp["id"]
            env.store_state_in_local(state)
            env.store_state_in_cloud(state)
            app_secrets = AzureDirectoyPasswordService(azure_token=azure_token, state=service_state)
            app_secrets.create(object_id=sp["id"], password_name="pbi")
            app_secrets.create(object_id=sp["id"], password_name="azf")
        else:
            app_svc.update(object_id=object_id, details=details)
    powerbi = content.get("spec").get("sidecars").get('powerbi', {})
    if powerbi:
        azure_token = get_azure_token()
        swa_settings = AzureSWASettingsAppService(azure_token=azure_token, state=service_state)
        organization_id = service_state['api']['organization_id']
        workspace_key = service_state['api']['workspace_key']
        secret_powerbi = env.get_project_secret(organization_id=organization_id,
                                                workspace_key=workspace_key,
                                                name="pbi")
        ext_args = dict(github_secret=github_secret, secret_powerbi=secret_powerbi)
        content = env.fill_template(data=file_content, state=state, ext_args=ext_args)
        powerbi = content.get("spec").get("sidecars").get('powerbi', {})
        settings = powerbi.get('settings')
        settings_str = json.dumps(obj=settings, indent=4, ensure_ascii=True)
        swa_settings.update(webapp_name=swa_name, details=settings_str)
    function_spec = sidecars.get("azure").get("function")
    if function_spec:
        url_zip = function_spec.get('url_zip')
        azure_credential = get_azure_credentials()
        arm_client = ResourceManagementClient(credential=azure_credential, subscription_id=subscription_id)
        azf_secret = env.get_project_secret(organization_id=organization_id, workspace_key=workspace_key, name="azf")
        arm_svc = ArmService(arm_client=arm_client, state=service_state)
        ext_args = dict(azure_app_client_secret=azf_secret, url_zip=url_zip)
        arm_svc.run(deployment_name="funcappmyde", file="azf_deploy.json", ext_args=ext_args)
    if not swa.get('id'):
        sys.exit(1)
