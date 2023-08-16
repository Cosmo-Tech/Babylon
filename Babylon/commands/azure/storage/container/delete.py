import logging

from azure.core.exceptions import HttpResponseError
from azure.storage.blob import BlobServiceClient
from click import argument
from click import command
from click import option
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.clients import pass_blob_client

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
@pass_blob_client
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
@argument("name", type=QueryType())
def delete(blob_client: BlobServiceClient, name: str, force_validation: bool = False) -> CommandResponse:
    """
    Delete a blob storage container
    """
    if not force_validation and not confirm_deletion("container", name):
        return CommandResponse.fail()
    try:
        container = blob_client.get_container_client(name)
        container.delete_container()
    except HttpResponseError as e:
        error_message = e.message.split("\n")
        logging.error(f"Failed to delete container '{name}': {error_message[0]}")
        return CommandResponse.fail()
    logger.info("Successfully deleted")
    return CommandResponse.success()
