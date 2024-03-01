import logging
import pathlib

from click import Path
from click import option
from click import command
from click import argument
from typing import Any, Optional
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.commands.azure.staticwebapp.services.api import AzureSWAService

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
@retrieve_state
def create(
    state: Any,
    azure_token: str,
    webapp_name: str,
    swa_file: Optional[pathlib.Path] = None,
) -> CommandResponse:
    """
    Create a static webapp data in the given resource group
    https://learn.microsoft.com/en-us/rest/api/appservice/static-sites/create-or-update-static-site
    """
    service_state = state['services']
    service = AzureSWAService(azure_token=azure_token, state=service_state)
    response = service.create(
        webapp_name=webapp_name,
        swa_file=swa_file,
    )
    return CommandResponse.success(response, verbose=True)
