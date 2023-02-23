import logging
from typing import Optional

from azure.core.exceptions import HttpResponseError
from azure.storage.blob import BlobServiceClient
from click import argument
from click import command

from ........utils.decorators import timing_decorator
from ........utils.typing import QueryType
from ........utils.clients import pass_blob_client

logger = logging.getLogger("Babylon")


@command()
@pass_blob_client
@timing_decorator
@argument("container_name", type=QueryType())
def create(blob_client: BlobServiceClient, container_name: str) -> Optional[str]:
    """Creates a new storageblob container with the given name"""
    logger.info(f"Creating container {container_name} in storage account {blob_client.account_name}")
    try:
        container = blob_client.create_container(container_name)
    except HttpResponseError as e:
        error_message = e.message.split("\n")
        logging.error(f"Failed to create container '{container_name}': {error_message[0]}")
        return
    except Exception as e:
        logger.error(e.message)
        return

    logger.info(f"Successfully created container {container_name}: {container.url}")
    return container.url
