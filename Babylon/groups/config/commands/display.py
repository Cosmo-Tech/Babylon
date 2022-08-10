import logging

from click import command

from ....utils.configuration import Configuration
from ....utils.decorators import pass_config

logger = logging.getLogger("Babylon")


@command()
@pass_config
def display(config: Configuration):
    """Display current config"""
    logger.info(str(config))
