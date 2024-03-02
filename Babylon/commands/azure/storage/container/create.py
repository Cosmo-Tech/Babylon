import logging

from azure.storage.blob import BlobServiceClient
from click import argument
from click import command
from Babylon.commands.azure.storage.services.container import AzureStorageContainerService
from Babylon.utils.decorators import timing_decorator, injectcontext

from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_blob_client

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@timing_decorator
@pass_blob_client
@argument("name", type=str)
def create(blob_client: BlobServiceClient, name: str) -> CommandResponse:
    """
    Creates a blob storage container
    """
    service = AzureStorageContainerService(blob_client=blob_client)
    response = service.create(name=name)
    return CommandResponse({"name": name, "url": response.url})
