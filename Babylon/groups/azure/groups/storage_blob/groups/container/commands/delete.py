from azure.core.exceptions import HttpResponseError
from azure.storage.blob import BlobServiceClient
from click import argument
from click import command
from click import confirm
from click import make_pass_decorator
from click import option
from click import prompt

import logging

logger = logging.getLogger("Babylon")

pass_blobclient = make_pass_decorator(BlobServiceClient)


@command()
@pass_blobclient
@argument("container_name")
@option("-f", "--force", "force_validation", is_flag=True, help="Don't ask for validation before delete")
def delete(blobclient: BlobServiceClient, container_name: str, force_validation: bool = False):
    """Deletes a storageblob container with the given name"""
    if not force_validation:
        if not confirm(f"You are trying to delete container {container_name} \nDo you want to continue ?"):
            logger.info("Container deletion aborted.")
            return

        confirm_container_name = prompt("Confirm Container name")
        if confirm_container_name != container_name:
            logger.error("Wrong Container name , "
                         "the id must be the same as the one that has been provide in delete command argument")
            return
    try:
        container = blobclient.get_container_client(container_name)
        container.delete_container()
    except HttpResponseError as e:
        error_message = e.message.split("\n")
        logging.error(f"Failed to delete container '{container_name}': {error_message[0]}")
        return
    logger.info(f"Successfully deleted container {container_name}")
