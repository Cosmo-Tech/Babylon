import logging

from typing import Any
from click import command
from click import argument
from click import option
from Babylon.commands.azure.staticwebapp.custom_domain.service.api import (
    AzureSWACustomDomainService,
)
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("webapp_name", type=QueryType())
@argument("domain_name", type=QueryType())
@inject_context_with_resource({"azure": ["resource_group_name", "subscription_id"]})
def delete(
    context: Any,
    azure_token: str,
    webapp_name: str,
    domain_name: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete static webapp data from a resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/delete-static-site-custom-domain
    """
    api_swa_custom_domain = AzureSWACustomDomainService(azure_token=azure_token, state=context)
    api_swa_custom_domain.delete(
        webapp_name=webapp_name,
        domain_name=domain_name,
        force_validation=force_validation,
    )
    return CommandResponse.success()
