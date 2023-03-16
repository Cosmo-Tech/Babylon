import logging

from click import argument
from click import command

from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("plugin", type=str)
def deactivate(plugin: str) -> CommandResponse:
    """Deactivate PLUGIN"""
    config = Environment().configuration
    plugins = list(config.get_available_plugin())
    if plugin in plugins:
        config.deactivate_plugin(plugin)
        logger.info(f"Plugin {plugin} was deactivated.")
        return CommandResponse.success()
    logger.error(f"Plugin {plugin} does not exists.")
    return CommandResponse.fail()