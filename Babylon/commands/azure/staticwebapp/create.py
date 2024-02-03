import logging
import pathlib
from typing import Any, Optional

from click import command, pass_context
from click import argument
from click import Path
from click import option
from Babylon.commands.azure.staticwebapp.service.api import AzureSWAService

from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_context
@pass_azure_token()
@option(
    "--file",
    "swa_file",
    type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
    help="Your custom staticwebapp description file yaml",
)
@option(
    "--select",
    "select",
    is_flag=True,
    default=True,
    help="Save this new staticwebapp in your configuration",
)
@argument("webapp_name", type=QueryType())
@inject_context_with_resource({"azure": ["resource_group_name", "subscription_id"]})
def create(
    ctx: Any,
    context: Any,
    azure_token: str,
    webapp_name: str,
    select: bool,
    swa_file: Optional[pathlib.Path] = None,
) -> CommandResponse:
    """
    Create a static webapp data in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    api_swa = AzureSWAService()
    response = api_swa.create(
        webapp_name=webapp_name,
        context=context,
        swa_file=swa_file,
        azure_token=azure_token,
    )
    return CommandResponse.success(response, verbose=True)
