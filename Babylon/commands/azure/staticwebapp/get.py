import logging
from typing import Any

from click import command, option
from click import argument
from Babylon.commands.azure.staticwebapp.service.api import AzureSWAService
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
@option(
    "--select",
    "select",
    is_flag=True,
    default=True,
    help="Save this new connector in your configuration",
)
@argument("webapp_name", type=QueryType())
@inject_context_with_resource({"azure": ["resource_group_name", "subscription_id"]})
def get(
    context: Any, azure_token: str, select: bool, webapp_name: str
) -> CommandResponse:
    """
    Get static webapp data from a resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/get-static-site
    """
    api_swa = AzureSWAService()
    response = api_swa.get(
        webapp_name=webapp_name, context=context, azure_token=azure_token
    )
    return CommandResponse.success(response, verbose=True)
