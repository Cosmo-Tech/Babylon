import logging

from click import argument
from click import command

from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("plugin", type=str)
def remove(plugin: str) -> CommandResponse:
    """Remove PLUGIN"""
    config = Environment().configuration
    plugins = list(config.get_available_plugin())
    if plugin in plugins:
        config.remove_plugin(plugin)
        logger.info(f"Plugin {plugin} was removed.")
        return CommandResponse.success()
    logger.error(f"Plugin {plugin} does not exists.")
    return CommandResponse.fail()
