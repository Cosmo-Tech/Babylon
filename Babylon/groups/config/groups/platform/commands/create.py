import logging

from click import argument
from click import command

from ......utils.environment import Environment
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("platform", nargs=1, type=str)
def create(platform: str) -> CommandResponse:
    config = Environment().configuration
    """Create a new platform file PLATFORM.yaml and open editor to edit it"""
    config.create_platform(platform)
    return CommandResponse()
