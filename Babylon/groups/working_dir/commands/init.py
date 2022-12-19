import logging

from click import command

from ....utils.decorators import timing_decorator
from ....utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
def init():
    """Initialize the current working_dir"""
    working_dir = Environment().working_dir
    if working_dir.is_zip:
        logger.error("You can't initialize a zip based working_dir.")
    else:
        working_dir.copy_template()
