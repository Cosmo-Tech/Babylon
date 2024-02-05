import logging
import pathlib

from typing import Any
from click import command
from click import argument
from click import Path
from Babylon.commands.webapp.service.api import AzureWebAppService
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@argument("file", type=Path(path_type=pathlib.Path, exists=True))
@inject_context_with_resource({'github': ['branch', 'repository']})
def upload_file(context: Any, file: pathlib.Path) -> CommandResponse:
    """
    Upload a file to the webapp github repository
    """
    # Get parent git repository of the workflow file
    api_web_app = AzureWebAppService(state=context)
    api_web_app.upload_file(file=file)
    return CommandResponse.success()
