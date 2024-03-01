import logging
import pathlib
from typing import Any

from click import Path
from click import option
from click import argument
from click import command, pass_context
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, retrieve_state, wrapcontext
from Babylon.commands.azure.ad.services.app import AzureDirectoyAppService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_context
@output_to_file
@pass_azure_token("graph")
@option(
    "--file",
    "registration_file",
    type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
    help="path file payload",
)
@argument("name", type=QueryType())
@retrieve_state
def create(state: Any, azure_token: str, name: str, registration_file: pathlib.Path) -> CommandResponse:
    """
    Register an app in Active Directory
    https://learn.microsoft.com/en-us/graph/api/application-post-applications
    """
    service_state = state['services']
    service = AzureDirectoyAppService(azure_token=azure_token, state=service_state)
    response = service.create(name=name, registration_file=registration_file)
    return CommandResponse.success(response, verbose=True)
