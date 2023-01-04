import logging
import pathlib
from typing import Optional

import click
from click import argument
from click import command

from ......utils.environment import Environment
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("platform",
          required=False,
          type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
def edit(platform: Optional[pathlib.Path] = None) -> CommandResponse:
    """Open editor to edit variables in given platform

    will open default platform if no argument is passed"""
    config = Environment().configuration
    if platform:
        config.edit_platform(platform)
    else:
        config.edit_platform(config.get_platform_path())
    return CommandResponse.success()
