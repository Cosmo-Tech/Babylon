import logging

from click import command

from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
def display() -> CommandResponse:
    """Display current config"""
    logger.info(str(Environment().configuration))
    return CommandResponse()
