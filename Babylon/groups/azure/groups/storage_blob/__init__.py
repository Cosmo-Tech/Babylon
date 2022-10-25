import logging
from azure.storage.blob import BlobServiceClient
from click import group
from click import pass_context
from click.core import Context

from .commands import list_commands
from .groups import list_groups
from .....utils.decorators import require_deployment_key

logger = logging.getLogger()


@group()
@pass_context
@require_deployment_key("storage_account_name", "storage_account_name")
def storage_blob(ctx: Context, storage_account_name: str):
    """Group interacting with Azure Storage Blob"""
    logger.info(f"Connecting to storage account '{storage_account_name}'")
    account_url = f"https://{storage_account_name}.blob.core.windows.net"
    blob_client = BlobServiceClient(account_url, ctx.parent.obj)
    ctx.obj = blob_client


for _command in list_commands:
    storage_blob.add_command(_command)

for _group in list_groups:
    storage_blob.add_command(_group)
