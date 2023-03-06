import logging
from typing import Optional

from azure.storage.blob import BlobServiceClient
from click import command

from .....utils.decorators import timing_decorator
from .....utils.clients import pass_blob_client

logger = logging.getLogger("Babylon")


@command()
@pass_blob_client
@timing_decorator
def get_all(blob_client: BlobServiceClient) -> Optional[str]:
    """Lists storage containers from a given account"""
    logger.info(f"Listing containers from storage account {blob_client.account_name}")
    try:
        containers = blob_client.list_containers()
    except Exception as e:
        logger.error(e.message)
        return None
    logger.info("Containers found:")
    account_url = f"https://{blob_client.account_name}.blob.core.windows.net"
    for container in containers:
        logger.info(f"  - {container.name}: {account_url}/{container.name}")
