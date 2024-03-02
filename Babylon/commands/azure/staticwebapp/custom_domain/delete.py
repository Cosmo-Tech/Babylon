import logging

from typing import Any
from click import command
from click import argument
from click import option
from Babylon.commands.azure.staticwebapp.services.custom_domain import (
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
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("webapp_name", type=str)
@argument("domain_name", type=str)
@retrieve_state
def delete(
    state: Any,
    azure_token: str,
    webapp_name: str,
    domain_name: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete static webapp data from a resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/delete-static-site-custom-domain
    """
    service_state = state['services']
    service = AzureSWACustomDomainService(azure_token=azure_token, state=service_state)
    service.delete(
        webapp_name=webapp_name,
        domain_name=domain_name,
        force_validation=force_validation,
    )
    return CommandResponse.success()
