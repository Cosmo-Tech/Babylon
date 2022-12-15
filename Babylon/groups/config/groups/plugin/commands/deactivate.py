import logging

from click import argument
from click import command

from ......utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@argument("plugin", type=str)
def deactivate(plugin: str):
    """Deactivate PLUGIN"""
    config = Environment().configuration
    plugins = list(config.get_available_plugin())
    if plugin in plugins:
        config.deactivate_plugin(plugin)
        logger.info(f"Plugin {plugin} was deactivated.")
    else:
        logger.error(f"Plugin {plugin} does not exists.")
