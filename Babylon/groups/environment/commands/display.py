import logging

from click import command
from click import pass_obj

from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@pass_obj
@timing_decorator
def display(environment):
    """Display information about the current environment"""
    logger.info(str(environment))
