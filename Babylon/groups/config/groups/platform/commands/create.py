import logging

from click import argument
from click import command

from ......utils.configuration import Configuration
from ......utils.decorators import pass_config

logger = logging.getLogger("Babylon")


@command()
@pass_config
@argument("platform", nargs=1, type=str)
def create(config: Configuration, platform: str):
    """Create a new platform file PLATFORM.yaml and open editor to edit it"""
    config.create_platform(platform)
