import logging
import pathlib

from typing import Any
from click import command
from click import argument
from click import Path
from Babylon.commands.webapp.service.api import AzureWebAppService
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@argument("destination_folder", type=Path(path_type=pathlib.Path))
@retrieve_state
def download(state: Any, destination_folder: pathlib.Path) -> CommandResponse:
    """
    Download the github repository locally
    """
    service = AzureWebAppService(state=state)
    service.download(destination_folder=destination_folder)
    return CommandResponse.success()
