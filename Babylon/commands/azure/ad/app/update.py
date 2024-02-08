import logging
import pathlib
from typing import Any

from click import Path
from click import option
from click import command
from click import argument
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.commands.azure.ad.app.service.api import AzureDirectoyAppService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token("graph")
@option(
    "--file",
    "registration_file",
    type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
    required=True,
    help="Your custom app description file yaml",
)
@argument("object_id", type=QueryType())
@retrieve_state
def update(
    state: Any, azure_token: str, object_id: str, registration_file: str
) -> CommandResponse:
    """
    Update an app registration in Active Directory
    https://learn.microsoft.com/en-us/graph/api/application-update
    """
    service = AzureDirectoyAppService(azure_token=azure_token, state=state)
    service.update(
        object_id=object_id,
        registration_file=registration_file,
    )
    return CommandResponse.success(None, verbose=True)
