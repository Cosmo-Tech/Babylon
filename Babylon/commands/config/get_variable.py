import logging

from click import command
from click import argument
from click import Choice

from ...utils.environment import Environment
from ...utils.response import CommandResponse
from ...utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@argument("location", type=Choice(["deploy", "platform", "secrets"]))
@argument("key", type=QueryType())
def get_variable(location: str, key: str) -> CommandResponse:
    """Set a configuration variable"""
    env = Environment()
    value = env.convert_data_query(f"%{location}%{key}")
    if value is None:
        logger.error(f"Could not find variable {key} from {location}")
        return CommandResponse.fail()
    return CommandResponse.success({"value": value}, verbose=True)
