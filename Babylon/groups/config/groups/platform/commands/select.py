import logging
import pathlib
from typing import Optional

import click
from click import argument
from click import command

from ......utils.configuration import Configuration
from ......utils.decorators import pass_config
from ......utils.interactive import select_from_list

logger = logging.getLogger("Babylon")


@command()
@pass_config
@argument("platform", required=False, type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
def select(config: Configuration, platform: Optional[pathlib.Path] = None):
    """Change current selected platform

    if not argument is passed will run in interactive mode"""

    if platform:
        if config.set_platform(platform):
            logger.info("Configuration successfully updated")
        else:
            logger.error(f"Configuration was not updated. {platform} is not a valid platform file.")
    else:
        logger.debug("Interactive change of platform:")
        available_platforms = list(config.list_platforms())
        new_platform = select_from_list(available_platforms, config.platform)
        if new_platform:
            config.set_platform(new_platform)
            logger.debug("Configuration successfully updated")
        else:
            logger.error("Issue while selecting new platform configuration")
