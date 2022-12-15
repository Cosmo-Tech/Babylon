import logging

from click import command

from ....utils.environment import Environment
from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
def validate():
    """Validate the current working_dir"""
    working_dir = Environment().working_dir
    env_is_ok = working_dir.compare_to_template(update_if_error=False)
    if env_is_ok:
        logger.info("working_dir is correct")
    else:
        logger.error("Issues were found with the working_dir, please check the logs")
