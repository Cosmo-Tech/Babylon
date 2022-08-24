import logging

from click import command

from ....utils.decorators import pass_solution
from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@pass_solution
@timing_decorator
def validate(solution):
    """Validate the current solution"""
    env_is_ok = solution.compare_to_template(update_if_error=False)
    if env_is_ok:
        logger.info("solution is correct")
    else:
        logger.error("Issues were found with the solution, please check the logs")
