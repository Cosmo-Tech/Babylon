import logging
import pathlib
from typing import Optional

import click
from click import argument
from click import command

from ......utils.configuration import Configuration
from ......utils.decorators import pass_config

logger = logging.getLogger("Babylon")


@command()
@pass_config
@argument("platform",
          required=False,
          type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
def edit(config: Configuration, platform: Optional[pathlib.Path] = None):
    """Open editor to edit variables in given platform

    will open default platform if no argument is passed"""
    if platform:
        config.edit_platform(platform)
    else:
        config.edit_platform(config.get_platform_path())
