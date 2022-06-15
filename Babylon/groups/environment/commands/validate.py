import logging

from click import command
from click import pass_obj

from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@pass_obj
@timing_decorator
def validate(environment):
    """Validate the current environment"""
    env_is_ok = environment.check_template(update_if_error=False)
    if env_is_ok:
        logger.info("Environment is correct")
    else:
        logger.error("Issues were found with the environment, please check the logs")
