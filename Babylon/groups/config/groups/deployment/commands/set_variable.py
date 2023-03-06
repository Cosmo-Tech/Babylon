import logging

from click import command
from click import argument

from ......utils.environment import Environment
from ......utils.response import CommandResponse
from ......utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@argument("variable_key", type=QueryType())
@argument("variable_value", type=QueryType())
def set_variable(variable_key: str, variable_value: str):
    """Set a deployment variable with a new value"""
    env = Environment()
    env.configuration.set_deploy_var(variable_key, variable_value)
    return CommandResponse.success()
