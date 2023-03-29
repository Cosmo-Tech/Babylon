import logging

from click import argument
from click import command

from .....utils.decorators import timing_decorator
from .....utils.typing import QueryType
from .....utils.response import CommandResponse
from .....utils.decorators import require_platform_key
from .....utils.credentials import pass_azure_token
from .....utils.request import oauth_request

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("storage")
@require_platform_key("storage_account_name")
@timing_decorator
@argument("container_name", type=QueryType())
def create(azure_token: str, storage_account_name: str, container_name: str) -> CommandResponse:
    """Creates a new storageblob container with the given name"""
    logger.info(f"Creating container {container_name} in storage account {storage_account_name}")
    account_url = f"https://{storage_account_name}.blob.core.windows.net"
    version_header = {"x-ms-version": "2017-11-09"}
    response = oauth_request(f"{account_url}/{container_name}?restype=container",
                             azure_token,
                             type="PUT",
                             headers=version_header)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Storage container {container_name} creation has been successfully launched")
    return CommandResponse.success()
