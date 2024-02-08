import logging
import pathlib

from typing import Any, Optional
from click import command, argument, option, Path
from Babylon.commands.azure.appinsight.service.api import AzureAppInsightService
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token()
@option(
    "--file",
    "file",
    type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
    help="Your custom appinsight description file yaml",
)
@argument("name", type=QueryType())
@retrieve_state
def create(
    state: Any, azure_token: str, name: str, file: Optional[pathlib.Path] = None
) -> CommandResponse:
    """
    Create a app insight resource in the given resource group
    https://learn.microsoft.com/en-us/rest/api/application-insights/components/create-or-update
    """
    service = AzureAppInsightService(azure_token=azure_token, state=state)
    output_data = service.create(name=name, file=file)
    return CommandResponse.success(output_data, verbose=True)
