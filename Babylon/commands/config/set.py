import logging

from typing import Any
from click import command, option
from click import argument
from click import Choice
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.config import config_files
from ruamel.yaml import YAML
from flatten_json import flatten, unflatten_list

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@option("--item", "items", multiple=True, type=str, help="Item <Key Value>")
@argument("resource", type=Choice(config_files))
@argument("key", type=QueryType())
@argument("value", type=QueryType(), required=False)
def set(resource: str, key: str, value: Any, items: list) -> CommandResponse:
    """
    Set a variable
    """
    yaml_loader = YAML()
    final = dict()
    data_file = env.configuration.config_dir / f"{env.context_id}.{env.environ_id}.{resource}.yaml"
    if not data_file.exists():
        logger.error("Configuration file not found")
        return CommandResponse.fail()

    with data_file.open(mode='r') as _f:
        data = yaml_loader.load(_f)

    result = flatten(data[env.context_id], separator=".")
    result.update({key: value})
    if len(items):
        del result[key]
        for i, k in enumerate(items):
            result.update({f"{key}.{i}": k})

    result = unflatten_list(result, separator=".")
    final[env.context_id] = result
    with data_file.open(mode='w') as _f:
        yaml_loader.dump(final, data_file)

    logger.info(f"Successfully set variable {key}")
    return CommandResponse.success()
