import logging

from click import command
from click import pass_obj

from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@pass_obj
@timing_decorator
def validate(solution):
    """Validate the current solution"""
    env_is_ok = solution.compare_to_template(update_if_error=False)
    if env_is_ok:
        logger.info("solution is correct")
    else:
        logger.error("Issues were found with the solution, please check the logs")
