import logging
from azure.storage.blob import BlobServiceClient
from click import group
from click import pass_context
from click import option
from click.core import Context

from .commands import list_commands
from .groups import list_groups
from .....utils.decorators import require_deployment_key

logger = logging.getLogger("Babylon")


@group()
@option("-a", "--account", "account", help="Storage account name")
@pass_context
@require_deployment_key("storage_account_name", "storage_account_name")
def storage_blob(ctx: Context, account: str, storage_account_name: str):
    """Group interacting with Azure Storage Blob"""
    account_name = account or storage_account_name
    logger.debug(f"Connecting to storage account '{account_name}'")
    account_url = f"https://{account_name}.blob.core.windows.net"
    blob_client = BlobServiceClient(account_url, ctx.parent.obj)
    ctx.obj = blob_client


for _command in list_commands:
    storage_blob.add_command(_command)

for _group in list_groups:
    storage_blob.add_command(_group)
