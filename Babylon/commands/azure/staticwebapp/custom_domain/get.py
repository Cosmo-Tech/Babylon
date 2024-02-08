import logging

from typing import Any
from click import command
from click import argument
from Babylon.commands.azure.staticwebapp.custom_domain.service.api import (
    AzureSWACustomDomainService,
)
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
@argument("domain_name", type=QueryType())
@retrieve_state
def get(
    state: Any, azure_token: str, webapp_name: str, domain_name: str
) -> CommandResponse:
    """
    Get a static webapp custom domain for the given static web app
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/get-static-site-custom-domain
    """
    service = AzureSWACustomDomainService(azure_token=azure_token, state=state)
    response = service.get(
        webapp_name=webapp_name,
        domain_name=domain_name,
    )
    return CommandResponse.success(response, verbose=True)
