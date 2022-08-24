import logging

from click import command

from ....utils.decorators import pass_working_dir
from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@pass_working_dir
@timing_decorator
def validate(working_dir):
    """Validate the current working_dir"""
    env_is_ok = working_dir.compare_to_template(update_if_error=False)
    if env_is_ok:
        logger.info("working_dir is correct")
    else:
        logger.error("Issues were found with the working_dir, please check the logs")
