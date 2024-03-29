import logging

from typing import Any
from click import command
from click import argument

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.commands.azure.staticwebapp.services.swa_api_svc import AzureSWAService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_azure_token()
@argument("webapp_name", type=str)
@retrieve_state
def get(state: Any, azure_token: str, webapp_name: str) -> CommandResponse:
    """
    Get static webapp data from a resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/get-static-site
    """
    service_state = state['services']
    service = AzureSWAService(azure_token=azure_token, state=service_state)
    response = service.get(webapp_name=webapp_name)
    return CommandResponse.success(response, verbose=True)
