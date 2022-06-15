import logging

from click import argument
from click import command
from click import pass_obj

from ....utils.decorators import timing_decorator
from ....utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@argument("target")
@pass_obj
@timing_decorator
def complete(environment: Environment):
    """Complete the current environment for missing elements"""
    environment.check_template(update_if_error=True)
