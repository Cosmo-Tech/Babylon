import logging

from click import command

from ....utils.decorators import pass_solution
from ....utils.decorators import timing_decorator
from ....utils.solution import Solution

logger = logging.getLogger("Babylon")


@command()
@pass_solution
@timing_decorator
def init(solution: Solution):
    """Initialize the current solution"""
    if solution.is_zip:
        logger.error("You can't initialize a zip based solution.")
    else:
        solution.copy_template()
