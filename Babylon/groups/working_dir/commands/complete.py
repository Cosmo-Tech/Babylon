import logging

from click import command

from ....utils.decorators import timing_decorator
from ....utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
def complete():
    """Complete the current working_dir for missing elements"""
    working_dir = Environment().working_dir

    if working_dir.is_zip:
        logger.error("You can't complete a zip based working_dir.\nValidate it instead.")
        return
    had_errors = working_dir.compare_to_template(update_if_error=True)
    if had_errors:
        logger.info("working_dir is correct, nothing was changed")
    else:
        logger.info("Issues were found with the working_dir")
        logger.info("Corrections were applied when necessary, please check the logs")
