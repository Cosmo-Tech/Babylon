import logging
import pathlib
from typing import Any

from click import Path
from click import option
from click import command

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, retrieve_state, injectcontext
from Babylon.commands.azure.ad.services.app import AzureDirectoyAppService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("graph")
@option(
    "--file",
    "registration_file",
    type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
    help="path file payload",
)
@retrieve_state
def create(state: Any, azure_token: str, registration_file: pathlib.Path) -> CommandResponse:
    """
    Register an app in Active Directory
    https://learn.microsoft.com/en-us/graph/api/application-post-applications
    """
    service_state = state['services']
    service = AzureDirectoyAppService(azure_token=azure_token, state=service_state)
    details = env.fill_template(registration_file.open().read(), state)
    response = service.create(details)
    return CommandResponse.success(response, verbose=True)
