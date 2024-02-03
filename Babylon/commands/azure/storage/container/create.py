import logging

from azure.storage.blob import BlobServiceClient
from click import argument
from click import command
from Babylon.commands.azure.storage.container.service.api import AzureStorageContainerService
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
    api_storage = AzureStorageContainerService(blob_client=blob_client)
    response = api_storage.create(name=name)
    return CommandResponse({"name": name, "url": response.url})
