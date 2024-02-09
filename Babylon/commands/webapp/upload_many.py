import logging
import pathlib

from typing import Optional
from typing import Any, Iterable
from click import command, option
from Babylon.utils.response import CommandResponse
from Babylon.commands.webapp.service.api import AzureWebAppService
from Babylon.utils.decorators import retrieve_state, wrapcontext

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@option("--file",
        "files",
        type=(pathlib.Path),
        multiple=True,
        help="Add a combination <Key Value> that will be sent as parameter to all your datasets")
@retrieve_state
def upload_many(
    state: Any,
    files: Optional[Iterable[pathlib.Path]] = None,
) -> CommandResponse:
    """
    Upload files to the webapp github repository
    """
    # Get parent git repository of the workflow file
    service_state = state['services']
    service = AzureWebAppService(state=service_state)
    service.upload_many(files=files)
    return CommandResponse.success()
