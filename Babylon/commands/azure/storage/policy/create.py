import logging
from typing import Any
from click import argument, command, option
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
@option("--days", type=int, default=365, help="Days after last modification", show_default=True)
@inject_context_with_resource({"azure": ['resource_group_name', 'storage_account_name']})
def create(context: Any, storage_mgmt_client: StorageManagementClient, days: int, account_name: str) -> CommandResponse:
    """
    Create or update default policy storage account
    """
    service = AzureStoragePolicyService(storage_mgmt_client=storage_mgmt_client)
    service.create(account_name=account_name, days=days)
    return CommandResponse.success()
