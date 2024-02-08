import logging

from typing import Any
from click import command
from click import argument
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.commands.azure.staticwebapp.service.api import AzureSWAService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@argument("webapp_name", type=QueryType())
@retrieve_state
def get(
    state: Any, azure_token: str, webapp_name: str
) -> CommandResponse:
    """
    Get static webapp data from a resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/get-static-site
    """
    service = AzureSWAService(azure_token=azure_token, state=state)
    response = service.get(webapp_name=webapp_name)
    return CommandResponse.success(response, verbose=True)
