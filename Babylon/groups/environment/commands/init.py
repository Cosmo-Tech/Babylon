import logging

from click import command
from click import pass_obj

from ....utils.decorators import timing_decorator
from ....utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@pass_obj
@timing_decorator
def init(environment: Environment):
    """Initialize the current environment"""
    environment.copy_template()
