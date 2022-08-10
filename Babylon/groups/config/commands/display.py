import logging

from click import command

from ....utils.config import Config
from ....utils.decorators import pass_config

logger = logging.getLogger("Babylon")


@command()
@pass_config
def display(config: Config):
    """Display current config"""
    logger.info(str(config))
