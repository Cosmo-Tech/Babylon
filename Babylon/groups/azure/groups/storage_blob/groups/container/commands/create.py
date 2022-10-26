import logging
from typing import Optional

from azure.core.exceptions import HttpResponseError
from azure.storage.blob import BlobServiceClient
from click import argument
from click import command
from click import make_pass_decorator

logger = logging.getLogger("Babylon")

pass_blobclient = make_pass_decorator(BlobServiceClient)


@command()
@pass_blobclient
@argument("container_name")
def create(blobclient: BlobServiceClient, container_name: str) -> Optional[str]:
    """Creates a new storageblob container with the given name"""
    logger.info(f"Creating container {container_name} in storage account {blobclient.account_name}")
    try:
        container = blobclient.create_container(container_name)
    except HttpResponseError as e:
        error_message = e.message.split("\n")
        logging.error(f"Failed to create container '{container_name}': {error_message[0]}")
        return
    except Exception as e:
        logger.error(e.message)
        return

    logger.info(f"Successfully created container {container_name}: {container.url}")
    return container.url
