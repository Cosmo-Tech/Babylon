import json
import logging
import pathlib

from typing import Optional
from click import command
from click import option
from click import Path
from Babylon.commands.webapp.service.api import AzureWebAppService
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file, wrapcontext

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@output_to_file
@option("--file",
        "config_file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        help="Your custom config description file yaml")
def export_config(config_file: Optional[pathlib.Path] = None) -> CommandResponse:
    """
    Export webapp configuration in a json file
    """
    service = AzureWebAppService()
    response = service.expor_config(config_file=config_file)
    return CommandResponse.success(json.loads(response))
