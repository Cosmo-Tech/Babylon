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
@argument("value", type=QueryType())
def set_variable(location: str, key: str, value: str) -> CommandResponse:
    """Set a configuration variable"""
    env = Environment()
    edit_map = {
        "deploy": env.configuration.set_deploy_var,
        "platform": env.configuration.set_platform_var,
        "secrets": lambda k, v: env.working_dir.set_encrypted_yaml_key(".secrets.yaml.encrypt", k, v)
    }
    edit_map[location](key.split("."), value)
    logger.info(f"Successfully set variable {key}: {value} in {location}")
    return CommandResponse.success()
