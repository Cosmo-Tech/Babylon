import logging

from click import command

from ....utils.decorators import pass_solution
from ....utils.decorators import timing_decorator
from ....utils.solution import Solution

logger = logging.getLogger("Babylon")


@command()
@pass_solution
@timing_decorator
def complete(solution: Solution):
    """Complete the current solution for missing elements"""

    if solution.is_zip:
        logger.error("You can't complete a zip based solution.\nValidate it instead.")
        return
    had_errors = solution.compare_to_template(update_if_error=True)
    if had_errors:
        logger.info("solution is correct, nothing was changed")
    else:
        logger.info("Issues were found with the solution")
        logger.info("Corrections were applied when necessary, please check the logs")
