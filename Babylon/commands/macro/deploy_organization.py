import os
import sys
import json

from logging import getLogger

import click
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import get_azure_token
from Babylon.commands.api.organizations.services.organization_api_svc import OrganizationService
from Babylon.commands.azure.storage.services.storage_container_svc import (
    AzureStorageContainerService, )

logger = getLogger("Babylon")
env = Environment()


def deploy_organization(namespace: str, file_content: str):
    _ret = [""]
    _ret.append("Organization deployment")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    platform_url, workspace_key, metadata = env.get_ns_from_text(content=namespace, file_content=file_content)
    state = env.retrieve_state_func(state_id=env.state_id)
    state["services"]["api"]["url"] = platform_url
    state['services']['azure']['tenant_id'] = env.tenant_id
    state["services"]["api"]["workspace_key"] = workspace_key
    azure_token = get_azure_token("csm_api")
    content = env.fill_template(data=file_content, state=state)
    payload: dict = content.get("spec").get("payload", {})
    state["services"]["api"]["organization_id"] = (payload.get("id") or state["services"]["api"]["organization_id"])
    spec = dict()
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    organization_service = OrganizationService(azure_token=azure_token, spec=spec, state=state["services"])
    sidecars = content.get("spec").get("sidecars", {})
    if not state["services"]["api"]["organization_id"]:
        logger.info("[api] creating organization")
        response = organization_service.create()
        organization = response.json()
        logger.info(f"[api] organization {organization['id']} successfully created")
        logger.info(json.dumps(organization, indent=2))
        service = AzureStorageContainerService(state=state, blob_client=env.blob_client)
        service.create(name=organization.get("id"))
    else:
        logger.info(f"[api] updating organization {state['services']['api']['organization_id']}")
        response = organization_service.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = organization_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        organization = response_json
        logger.info(json.dumps(organization, indent=2))
    state["services"]["api"]["organization_id"] = organization.get("id")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    run_scripts = sidecars.get("run_scripts")
    if run_scripts:
        data = run_scripts.get("post_deploy.sh", "")
        if data:
            os.system(data)
    if not organization.get("id"):
        sys.exit(1)
