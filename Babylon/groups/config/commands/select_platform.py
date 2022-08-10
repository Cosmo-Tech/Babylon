import logging
from typing import Optional

from click import argument
from click import command

from ....utils.config import Config
from ....utils.decorators import pass_config
from ....utils.interactive import select_from_list

logger = logging.getLogger("Babylon")


@command()
@pass_config
@argument("platform", required=False, type=str)
def select_platform(config: Config, platform: Optional[str] = None):
    """Change current selected platform

    if not argument is passed will run in interactive mode"""
    if platform:
        if config.set_deploy(platform):
            logger.info(f"Configuration successfully updated")
        else:
            logger.error(f"Configuration was not updated. {platform} is not a valid deploy name.")
    else:
        logger.debug("Interactive change of platform:")
        available_platforms = list(config.list_platforms())
        new_platform = select_from_list(available_platforms, config.platform)
        if new_platform:
            config.set_platform(new_platform)
            logger.debug(f"Configuration successfully updated")
        else:
            logger.error("Issue while selecting new platform configuration")
