import logging

from click import command
from click import pass_obj

from ....utils.decorators import timing_decorator
from ....utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@pass_obj
@timing_decorator
def complete(environment: Environment):
    """Complete the current environment for missing elements"""
    had_errors = environment.compare_to_template(update_if_error=True)
    if had_errors:
        logger.info("Environment is correct, nothing was changed")
    else:
        logger.info("Issues were found with the environment")
        logger.info("Corrections were applied when necessary, please check the logs")
