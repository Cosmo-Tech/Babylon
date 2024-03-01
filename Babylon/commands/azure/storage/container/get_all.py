import logging

from typing import Optional
from azure.storage.blob import BlobServiceClient
from click import command, option
from Babylon.commands.azure.storage.services.container import AzureStorageContainerService
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.clients import pass_blob_client
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@timing_decorator
@pass_blob_client
@option("--filter", "filter", help="Filter response with a jmespath query")
def get_all(blob_client: BlobServiceClient, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all blob storage containers
    """
    service = AzureStorageContainerService(blob_client=blob_client)
    response = service.get_all(filter=filter)
    return CommandResponse.success(response, verbose=True)
