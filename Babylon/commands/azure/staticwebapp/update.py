import logging
import pathlib

from typing import Any, Optional
from click import command
from click import argument
from click import option
from click import Path
from Babylon.commands.azure.staticwebapp.service.api import AzureSWAService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@option(
    "--file",
    "swa_file",
    type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
    help="Your custom staticwebapp description file yaml",
)
@argument("webapp_name", type=QueryType())
@inject_context_with_resource({"azure": ["resource_group_name", "subscription_id"]})
def update(
    context: Any,
    azure_token: str,
    webapp_name: str,
    swa_file: Optional[Path] = None,
) -> CommandResponse:
    """
    Update a static webapp data in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    api_swa = AzureSWAService()
    response = api_swa.update(
        webapp_name=webapp_name,
        context=context,
        swa_file=swa_file,
        azure_token=azure_token,
    )
    return CommandResponse.success(response, verbose=True)
