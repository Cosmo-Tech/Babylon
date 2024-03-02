import logging

from click import command
from click import argument
from click import Choice
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

from Babylon.config import config_files
from ruamel.yaml import YAML
from flatten_json import flatten

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@argument("resource", type=Choice(config_files))
@argument("key", type=str)
def get(resource: str, key: str) -> CommandResponse:
    """
    Get a variable
    """
    yaml_loader = YAML()
    data_file = env.configuration.config_dir / f"{env.context_id}.{env.environ_id}.{resource}.yaml"
    if not data_file.exists():
        logger.error("Configuration file not found")
        return CommandResponse.fail()
    with data_file.open(mode='r') as _f:
        data = yaml_loader.load(_f)
    result = flatten(data[env.context_id], separator=".")
    try:
        print(result[key])
    except KeyError as e:
        logger.info(f"key: {e} not found")
        logger.info(f"Check {env.pwd}.{env.context_id}.{env.environ_id}.{resource}.yaml file")
        return CommandResponse.fail()
    return CommandResponse.success()
