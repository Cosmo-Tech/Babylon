import logging

from click import command

from ....utils.environment import Environment
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
def display() -> CommandResponse:
    working_dir = Environment().working_dir
    """Display information about the current working_dir"""
    logger.info(str(working_dir))
    return CommandResponse()
