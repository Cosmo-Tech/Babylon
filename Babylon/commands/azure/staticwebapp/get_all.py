import logging

from typing import Any, Optional
from click import command, option
from Babylon.commands.azure.staticwebapp.service.api import AzureSWAService
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all static webapps within the subscription
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/list
    """
    service_state = state['services']
    service = AzureSWAService(azure_token=azure_token, state=service_state)
    response = service.get_all()
    return CommandResponse.success(response, verbose=True)
