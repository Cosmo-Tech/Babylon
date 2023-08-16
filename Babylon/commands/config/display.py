import logging

from click import command
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
def display() -> CommandResponse:
    """
    Display current configuration
    """
    config = Environment().configuration
    logger.info(str(config))
