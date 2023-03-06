import logging
import pathlib
from typing import Optional

import click
from click import argument
from click import command

from ....utils.environment import Environment
from ....utils.interactive import select_from_list
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("platform", required=False, type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
def select(platform: Optional[pathlib.Path] = None) -> CommandResponse:
    """Change current selected platform

    if not argument is passed will run in interactive mode"""
    config = Environment().configuration

    if platform:
        if config.set_platform(platform):
            logger.info("Configuration successfully updated")
            return CommandResponse.success()
        logger.error(f"Configuration was not updated. {platform} is not a valid platform file.")
        return CommandResponse.fail()
    logger.debug("Interactive change of platform:")
    available_platforms = list(config.list_platforms())
    new_platform = select_from_list(available_platforms, config.platform)
    if new_platform:
        config.set_platform(new_platform)
        logger.debug("Configuration successfully updated")
        return CommandResponse.success()
    logger.error("Issue while selecting new platform configuration")
    return CommandResponse.fail()
