import json

from logging import getLogger
from Babylon.services.blob import blob_client
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import get_azure_token
from Babylon.services.organizations_service import OrganizationService
from Babylon.commands.azure.storage.container.service.api import (
    AzureStorageContainerService,
)

logger = getLogger("Babylon")
env = Environment()


def deploy_organization(file_content: dict) -> bool:
    print("organization deployment")
    payload: dict = file_content.get("spec").get("payload")
    azure_token = get_azure_token("csm_api")
    state = env.retrieve_state_func()

    service_state = state["services"]
    service_state["api"]["organization_id"] = (
        payload.get("id") or service_state["api"]["organization_id"]
    )
    spec = dict()
    spec["payload"] = json.dumps(payload, indent=2, ensure_ascii=True)
    organization_service = OrganizationService(
        azure_token=azure_token, spec=spec, state=service_state
    )
    if not service_state["api"]["organization_id"]:
        response = organization_service.create()
        organization = response.json()
        # create container
        account_secret = env.get_platform_secret(
            platform=env.environ_id, resource="storage", name="account"
        )
        storage_name = state["services"]["azure"]["storage_account_name"]
        blob = blob_client(storage_name=storage_name, account_secret=account_secret)
        service = AzureStorageContainerService(state=state, blob_client=blob)
        logger.info(organization)
        logger.info("creating container ...")
        response = service.create(name=organization.get("id"))
    else:
        response = organization_service.update()
        response_json = response.json()
        old_security = response_json.get("security")
        security_spec = organization_service.update_security(old_security=old_security)
        response_json["security"] = security_spec
        organization = response_json
        logger.info(organization)
    state["services"]["api"]["organization_id"] = organization.get("id")
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    return organization.get("id") != ""
