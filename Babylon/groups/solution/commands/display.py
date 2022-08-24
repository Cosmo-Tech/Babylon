import logging

from click import command

from ....utils.decorators import pass_solution
from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@pass_solution
@timing_decorator
def display(solution):
    """Display information about the current solution"""
    logger.info(str(solution))
