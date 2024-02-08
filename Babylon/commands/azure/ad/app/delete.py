import logging

from click import command
from click import argument
from Babylon.utils.typing import QueryType
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.commands.azure.ad.app.service.api import AzureDirectoyAppService

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_azure_token("graph")
@argument("object_id", type=QueryType(), required=False)
def delete(object_id: str, azure_token: str) -> CommandResponse:
    """
    Delete an app in Active Directory
    https://learn.microsoft.com/en-us/graph/api/application-delete
    """
    service = AzureDirectoyAppService(azure_token=azure_token)
    service.delete(object_id)
    return CommandResponse.success(None, verbose=True)
