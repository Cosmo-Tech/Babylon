import logging

from click import argument
from click import command

from ......utils.configuration import Configuration
from ......utils.decorators import pass_config

logger = logging.getLogger("Babylon")


@command()
@pass_config
@argument("plugin", type=str)
def activate(config: Configuration, plugin: str):
    """Activate PLUGIN"""
    plugins = list(config.get_available_plugin())
    if plugin in plugins:
        config.activate_plugin(plugin)
        logger.info(f"Plugin {plugin} was activated.")
    else:
        logger.error(f"Plugin {plugin} does not exists.")
