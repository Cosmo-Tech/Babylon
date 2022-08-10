import logging

from click import command
from click import pass_obj

from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@pass_obj
@timing_decorator
def display(solution):
    """Display information about the current solution"""
    logger.info(str(solution))
