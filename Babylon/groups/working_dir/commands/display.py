import logging

from click import command

from ....utils.decorators import pass_working_dir
from ....utils.decorators import timing_decorator

logger = logging.getLogger("Babylon")


@command()
@pass_working_dir
@timing_decorator
def display(working_dir):
    """Display information about the current working_dir"""
    logger.info(str(working_dir))
