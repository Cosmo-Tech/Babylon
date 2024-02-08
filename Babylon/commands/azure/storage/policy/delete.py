import logging
from typing import Any
from click import argument, command
from Babylon.commands.azure.storage.policy.service.api import AzureStoragePolicyService
from Babylon.utils.clients import pass_storage_mgmt_client
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.response import CommandResponse
from azure.mgmt.storage import StorageManagementClient

from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_storage_mgmt_client
@argument("account_name", type=QueryType())
@retrieve_state
def delete(
    state: Any, storage_mgmt_client: StorageManagementClient, account_name: str
) -> CommandResponse:
    """
    Delete default policy storage account
    """
    service = AzureStoragePolicyService(
        storage_mgmt_client=storage_mgmt_client, state=state
    )
    service.delete(account_name=account_name)
    return CommandResponse.success()
