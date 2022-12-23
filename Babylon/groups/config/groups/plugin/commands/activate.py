import logging

from click import argument
from click import command

from ......utils.environment import Environment
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("plugin", type=str)
def activate(plugin: str) -> CommandResponse:
    """Activate PLUGIN"""
    config = Environment().configuration
    plugins = list(config.get_available_plugin())
    if plugin in plugins:
        config.activate_plugin(plugin)
        logger.info(f"Plugin {plugin} was activated.")
        return CommandResponse()
    logger.error(f"Plugin {plugin} does not exists.")
    return CommandResponse.fail()
