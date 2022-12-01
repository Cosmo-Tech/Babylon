import logging

from click import command

from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
def update() -> CommandResponse:
    """Command created from a template"""
    logger.warning("This command was initialized from a template and is empty")
    return CommandResponse()
