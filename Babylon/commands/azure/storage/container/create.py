import logging

from azure.storage.blob import BlobServiceClient
from click import argument, command

from Babylon.commands.azure.storage.services.storage_container_svc import AzureStorageContainerService
from Babylon.utils.clients import pass_blob_client
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_blob_client
@argument("name", type=str)
def create(blob_client: BlobServiceClient, name: str) -> CommandResponse:
    """
    Creates a blob storage container
    """
    service = AzureStorageContainerService(blob_client=blob_client)
    response = service.create(name=name)
    return CommandResponse({"name": name, "url": response.url})
