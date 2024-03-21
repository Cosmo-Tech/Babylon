import logging

from typing import Any
from click import command
from click import argument
from Babylon.commands.azure.staticwebapp.services.swa_custom_domain_svc import (
    AzureSWACustomDomainService, )
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_azure_token()
@argument("webapp_name", type=str)
@argument("domain_name", type=str)
@retrieve_state
def get(state: Any, azure_token: str, webapp_name: str, domain_name: str) -> CommandResponse:
    """
    Get a static webapp custom domain for the given static web app
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/get-static-site-custom-domain
    """
    service_state = state['services']
    service = AzureSWACustomDomainService(azure_token=azure_token, state=service_state)
    response = service.get(
        webapp_name=webapp_name,
        domain_name=domain_name,
    )
    return CommandResponse.success(response, verbose=True)
