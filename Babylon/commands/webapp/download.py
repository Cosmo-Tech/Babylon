import logging
import pathlib

from typing import Any
from click import command
from click import argument
from click import Path
from Babylon.commands.webapp.service.api import AzureWebAppService
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@argument("destination_folder", type=Path(path_type=pathlib.Path))
@inject_context_with_resource({'github': ['organization', 'repository', 'branch']})
def download(context: Any, destination_folder: pathlib.Path) -> CommandResponse:
    """
    Download the github repository locally
    """
    service = AzureWebAppService(state=context)
    service.download(destination_folder=destination_folder)
    return CommandResponse.success()
