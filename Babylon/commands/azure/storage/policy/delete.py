import logging
from typing import Any
from click import argument, command
from Babylon.commands.azure.storage.services.policy import AzureStoragePolicyService
from Babylon.utils.clients import pass_storage_mgmt_client
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.response import CommandResponse
from azure.mgmt.storage import StorageManagementClient



logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_storage_mgmt_client
@argument("account_name", type=str)
@retrieve_state
def delete(state: Any, storage_mgmt_client: StorageManagementClient, account_name: str) -> CommandResponse:
    """
    Delete default policy storage account
    """
    service_state = state['services']
    service = AzureStoragePolicyService(storage_mgmt_client=storage_mgmt_client, state=service_state)
    service.delete(account_name=account_name)
    return CommandResponse.success()
