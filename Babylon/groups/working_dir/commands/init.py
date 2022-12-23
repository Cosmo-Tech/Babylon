import logging

from click import command

from ....utils.decorators import timing_decorator
from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
def init() -> CommandResponse:
    """Initialize the current working_dir"""
    working_dir = Environment().working_dir
    if working_dir.is_zip:
        logger.error("You can't initialize a zip based working_dir.")
        return CommandResponse.fail()
    working_dir.copy_template()
    return CommandResponse()
