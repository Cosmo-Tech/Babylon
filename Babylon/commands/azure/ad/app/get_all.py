import logging

from click import option
from click import command
from typing import Any, Optional
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, retrieve_state, wrapcontext
from Babylon.commands.azure.ad.app.service.api import AzureDirectoyAppService

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@output_to_file
@pass_azure_token("graph")
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(
    state: Any, azure_token: str, filter: Optional[str] = None
) -> CommandResponse:
    """
    Get all apps registered in Active Directory
    https://learn.microsoft.com/en-us/graph/api/application-list
    """
    service = AzureDirectoyAppService(azure_token=azure_token, state=state)
    output_data = service.get_all(filter=filter)
    return CommandResponse.success(output_data, verbose=True)
