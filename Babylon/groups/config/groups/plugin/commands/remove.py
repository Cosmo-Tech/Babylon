import logging

from click import argument
from click import command

from ......utils.configuration import Configuration
from ......utils.decorators import pass_config

logger = logging.getLogger("Babylon")


@command()
@pass_config
@argument("plugin", type=str)
def remove(config: Configuration, plugin: str):
    """Remove PLUGIN"""
    plugins = list(config.get_available_plugin())
    if plugin in plugins:
        config.remove_plugin(plugin)
        logger.info(f"Plugin {plugin} was removed.")
    else:
        logger.error(f"Plugin {plugin} does not exists.")
