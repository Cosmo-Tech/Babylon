import logging
from typing import Any
from click import argument, command, option
from Babylon.commands.azure.storage.services.storage_policy_svc import AzureStoragePolicyService
from Babylon.utils.clients import pass_storage_mgmt_client
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.response import CommandResponse
from azure.mgmt.storage import StorageManagementClient

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_storage_mgmt_client
@argument("account_name", type=str)
@option(
    "--days",
    type=int,
    default=365,
    help="Days after last modification",
    show_default=True,
)
@retrieve_state
def create(
    state: Any,
    storage_mgmt_client: StorageManagementClient,
    days: int,
    account_name: str,
) -> CommandResponse:
    """
    Create or update default policy storage account
    """
    service_state = state['services']
    service = AzureStoragePolicyService(storage_mgmt_client=storage_mgmt_client, state=service_state)
    service.create(account_name=account_name, days=days)
    return CommandResponse.success()
