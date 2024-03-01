import logging
from typing import Any

from click import command
from click import argument
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.commands.azure.ad.services.app import AzureDirectoyAppService

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_azure_token("graph")
@argument("object_id", type=QueryType(), required=False)
@retrieve_state
def delete(state: Any, object_id: str, azure_token: str) -> CommandResponse:
    """
    Delete an app in Active Directory
    https://learn.microsoft.com/en-us/graph/api/application-delete
    """
    service_state = state['services']
    service = AzureDirectoyAppService(azure_token=azure_token, state=service_state)
    service.delete(object_id)
    return CommandResponse.success(None, verbose=True)
