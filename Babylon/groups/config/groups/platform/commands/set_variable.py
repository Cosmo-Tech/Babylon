import logging

from click import command
from click import argument

from ......utils.environment import Environment
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("variable_key")
@argument("variable_value")
def set_variable(variable_key: str, variable_value: str):
    """Set a platform variable with a new value"""
    env = Environment()
    env.configuration.set_platform_var(variable_key, variable_value)
    return CommandResponse()
