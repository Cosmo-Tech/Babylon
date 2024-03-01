import logging

from typing import Any
from click import command
from click import argument
from Babylon.commands.azure.staticwebapp.services.custom_domain import (
    AzureSWACustomDomainService, )
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@argument("webapp_name", type=QueryType())
@retrieve_state
def get_all(state: Any, azure_token: str, webapp_name: str) -> CommandResponse:
    """
    Get static webapp custom domains for the given static web app
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/list-static-site-custom-domains
    """
    service_state = state['services']
    service = AzureSWACustomDomainService(azure_token=azure_token, state=service_state)
    response = service.get_all(webapp_name=webapp_name)
    return CommandResponse.success(response, verbose=True)
