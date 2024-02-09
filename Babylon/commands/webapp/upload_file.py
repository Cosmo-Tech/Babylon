import logging
import pathlib

from typing import Any
from click import command
from click import argument
from click import Path
from Babylon.commands.webapp.service.api import AzureWebAppService
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import retrieve_state, wrapcontext

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@argument("file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_state
def upload_file(state: Any, file: pathlib.Path) -> CommandResponse:
    """
    Upload a file to the webapp github repository
    """
    # Get parent git repository of the workflow file
    service_state = state['services']
    service = AzureWebAppService(state=service_state)
    service.upload_file(file=file)
    return CommandResponse.success()
