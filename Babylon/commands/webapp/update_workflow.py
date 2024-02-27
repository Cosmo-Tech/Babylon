import logging
import pathlib

from click import Path
from click import command
from click import argument
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.commands.webapp.service.api import AzureWebAppService

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@argument("workflow_file", type=Path(path_type=pathlib.Path))
def update_workflow(workflow_file: pathlib.Path) -> CommandResponse:
    """
    Update a github workflow file to read environment from a config.json file during deployment
    """
    service = AzureWebAppService()
    service.update_workflow(workflow_file=workflow_file)
    return CommandResponse.success()
