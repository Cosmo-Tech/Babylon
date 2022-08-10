import logging
from typing import Optional

from click import argument
from click import command

from ......utils.configuration import Configuration
from ......utils.decorators import pass_config

logger = logging.getLogger("Babylon")


@command()
@pass_config
@argument("platform", required=False, type=str)
def edit(config: Configuration, platform: Optional[str] = None):
    """Open editor to edit variables in given platform

    will open default platform if no argument is passed"""
    if platform:
        config.edit_platform(platform)
    else:
        config.edit_platform(config.platform)
