import logging

from typing import Any, Optional
from click import command, option
from Babylon.commands.azure.staticwebapp.service.api import AzureSWAService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@option("--filter", "filter", help="Filter response with a jmespath query")
@inject_context_with_resource({"azure": ["resource_group_name", "subscription_id"]})
def get_all(
    context: Any, azure_token: str, filter: Optional[str] = None
) -> CommandResponse:
    """
    Get all static webapps within the subscription
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/list
    """
    service = AzureSWAService(azure_token=azure_token, state=context)
    response = service.get_all()
    return CommandResponse.success(response, verbose=True)
