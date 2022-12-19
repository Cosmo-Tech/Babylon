import logging

from click import command

from ....utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
def display():
    """Display current config"""
    logger.info(str(Environment().configuration))
