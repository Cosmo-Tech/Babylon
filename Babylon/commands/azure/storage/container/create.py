import logging

from azure.core.exceptions import HttpResponseError
from azure.storage.blob import BlobServiceClient
from click import argument
from click import command

from .....utils.decorators import timing_decorator
from .....utils.typing import QueryType
from .....utils.response import CommandResponse
from .....utils.clients import pass_blob_client

logger = logging.getLogger("Babylon")


@command()
@pass_blob_client
@argument("container_name", type=QueryType(), default="%deploy%organization_id")
@timing_decorator
def create(blob_client: BlobServiceClient, container_name: str) -> CommandResponse:
    """Creates a new storageblob container with the given name"""
    logger.info(f"Creating container {container_name} in storage account {blob_client.account_name}")
    container_name = container_name.lower()
    try:
        container = blob_client.create_container(container_name)
    except HttpResponseError as e:
        error_message = e.message.split("\n")
        logging.error(f"Failed to create container '{container_name}': {error_message[0]}")
        return CommandResponse.fail()
    except Exception as e:
        logger.error(e.message)
        return CommandResponse.fail()

    logger.info(f"Successfully created container {container_name}: {container.url}")
    return CommandResponse({"name": container_name, "url": container.url})
