import json

from logging import getLogger
import sys
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import get_azure_token
from Babylon.services.organizations_service import OrganizationService
from Babylon.commands.azure.storage.container.service.api import (
    AzureStorageContainerService, )

logger = getLogger("Babylon")
env = Environment()


def deploy_organization(file_content: str):
    logger.info("Organization deployment")
    state = env.retrieve_state_func()
    azure_token = get_azure_token("csm_api")
    content = env.fill_template(data=file_content, state=state)
    payload: dict = content.get("spec").get("payload", {})
    service_state = state["services"]
    service_state["api"]["organization_id"] = (payload.get("id") or service_state["api"]["organization_id"])
    spec = dict()
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    organization_service = OrganizationService(azure_token=azure_token, spec=spec, state=service_state)
    if not service_state["api"]["organization_id"]:
        logger.info("Creating organization...")
        response = organization_service.create()
        organization = response.json()
        logger.info(f"Organization {organization['id']} successfully created...")
        logger.info(json.dumps(organization, indent=2))
        service = AzureStorageContainerService(state=state, blob_client=env.blob_client)
        service.create(name=organization.get("id"))
    else:
        logger.info(f"Updating organization {service_state['api']['organization_id']}...")
        response = organization_service.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = organization_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        organization = response_json
        logger.info(json.dumps(organization, indent=2))
    state["services"]["api"]["organization_id"] = organization.get("id")
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    if not organization.get("id"):
        sys.exit(1)
