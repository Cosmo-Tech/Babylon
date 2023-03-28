import logging
from typing import Optional

from azure.storage.blob import BlobServiceClient
from click import command, option
import jmespath

from .....utils.decorators import timing_decorator
from .....utils.clients import pass_blob_client
from .....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_blob_client
@timing_decorator
@option("--filter", "filter", help="Filter response with a jmespath query")
def get_all(blob_client: BlobServiceClient, filter: Optional[str] = None) -> CommandResponse:
    """Get all storage containers from a given account"""
    logger.info(f"Listing containers from storage account {blob_client.account_name}")
    try:
        containers = blob_client.list_containers()
    except Exception as e:
        logger.error(e.message)
        return CommandResponse.fail()
    output_data = [{
        "name": container.name,
        "lease": container.lease,
        "etag": container.etag,
        "deleted": container.deleted,
        "public_access": container.public_access
    } for container in containers]
    if filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)