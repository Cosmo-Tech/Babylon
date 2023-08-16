import logging

from azure.core.exceptions import HttpResponseError
from azure.storage.blob import BlobServiceClient
from click import argument
from click import command
from Babylon.utils.checkers import check_ascii
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_blob_client

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@timing_decorator
@pass_blob_client
@argument("name", type=QueryType())
def create(blob_client: BlobServiceClient, name: str) -> CommandResponse:
    """
    Creates a blob storage container
    """
    check_ascii(name)
    logger.info(f"Creating container {name} in storage account {blob_client.account_name}")
    name = name.lower()
    try:
        container = blob_client.create_container(name)
    except HttpResponseError as e:
        error_message = e.message.split("\n")
        logging.error(f"Failed to create container '{name}': {error_message[0]}")
        return CommandResponse.fail()
    except Exception as e:
        logger.error(e.message)
        return CommandResponse.fail()

    logger.info("Successfully created")
    return CommandResponse({"name": name, "url": container.url})
