import logging

from typing import Any
from click import command
from click import argument
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
@argument("webapp_name", type=QueryType())
@inject_context_with_resource({"azure": ["resource_group_name", "subscription_id"]})
def get_all(context: Any, azure_token: str, webapp_name: str) -> CommandResponse:
    """
    Get static webapp custom domains for the given static web app
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/list-static-site-custom-domains
    """
    api_swa_custom_domain = AzureSWACustomDomainService(azure_token=azure_token, state=context)
    response = api_swa_custom_domain.get_all(
        webapp_name=webapp_name
    )
    return CommandResponse.success(response, verbose=True)
