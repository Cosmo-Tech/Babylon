import logging

from click import command

from ...utils.environment import Environment
from ...utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
def display() -> CommandResponse:
    """Display current config"""
    config = Environment().configuration
    logger.info(str(config))
    return CommandResponse.success({"deployment": config.get_deploy(), "platform": config.get_platform()})
