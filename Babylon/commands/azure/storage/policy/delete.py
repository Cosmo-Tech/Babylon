import logging
from typing import Any
from click import argument, command
from Babylon.commands.azure.storage.policy.service.api import AzureStoragePolicyService
from Babylon.utils.clients import pass_storage_mgmt_client
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.response import CommandResponse
from azure.mgmt.storage import StorageManagementClient

from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_storage_mgmt_client
@argument("account_name", type=QueryType())
@inject_context_with_resource({"azure": ["resource_group_name"]})
def delete(
    context: Any, storage_mgmt_client: StorageManagementClient, account_name: str
) -> CommandResponse:
    """
    Delete default policy storage account
    """
    api_storage_policy = AzureStoragePolicyService(storage_mgmt_client=storage_mgmt_client)
    api_storage_policy.delete(account_name=account_name, context=context)
    return CommandResponse.success()
