import logging
from typing import Optional

from azure.storage.blob import BlobServiceClient
from click import command
from click import make_pass_decorator

from ........utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")

pass_blobclient = make_pass_decorator(BlobServiceClient)


@command()
@pass_blobclient
@timing_decorator
def get_all(blobclient: BlobServiceClient) -> Optional[str]:
    """Lists storage containers from a given account"""
    logger.info(f"Listing containers from storage account {blobclient.account_name}")
    try:
        containers = blobclient.list_containers()
    except Exception as e:
        logger.error(e.message)
        return None
    logger.info("Containers found:")
    account_url = f"https://{blobclient.account_name}.blob.core.windows.net"
    for container in containers:
        logger.info(f"  - {container.name}: {account_url}/{container.name}")
