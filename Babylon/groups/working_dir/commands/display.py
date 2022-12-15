import logging

from click import command

from ....utils.environment import Environment
from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
def display():
    working_dir = Environment().working_dir
    """Display information about the current working_dir"""
    logger.info(str(working_dir))
