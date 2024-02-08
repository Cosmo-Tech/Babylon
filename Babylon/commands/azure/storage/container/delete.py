import logging

from azure.storage.blob import BlobServiceClient
from click import argument
from click import command
from click import option
from Babylon.commands.azure.storage.container.service.api import AzureStorageContainerService
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.clients import pass_blob_client

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@timing_decorator
@pass_blob_client
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("name", type=QueryType())
def delete(
    blob_client: BlobServiceClient, name: str, force_validation: bool = False
) -> CommandResponse:
    """
    Delete a blob storage container
    """
    service = AzureStorageContainerService(blob_client=blob_client)
    service.delete(name=name, force_validation=force_validation)
    return CommandResponse.success()
