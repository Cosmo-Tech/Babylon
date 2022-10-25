import logging
from typing import Optional

from azure.core.exceptions import HttpResponseError
from azure.storage.blob import BlobServiceClient
from click import command
from click import make_pass_decorator

logger = logging.getLogger("Babylon")

pass_blobclient = make_pass_decorator(BlobServiceClient)


@command()
@pass_blobclient
def list(blobclient: BlobServiceClient) -> Optional[str]:
    """Creates a new storageblob container with the given name"""
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
