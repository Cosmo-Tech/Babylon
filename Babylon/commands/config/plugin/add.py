import logging
import pathlib

import click
from click import argument
from click import command

from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("plugin_path", type=click.Path(file_okay=False, dir_okay=True, readable=True, path_type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path)))
def add(plugin_path: pathlib.Path) -> CommandResponse:
    """Add a plugin found at PLUGIN_PATH"""
    config = Environment().configuration
    plugin_name = config.add_plugin(plugin_path)
    if plugin_name:
        logger.info(f"Plugin {plugin_name} was added to config.")
        return CommandResponse.success()
    logger.error("Plugin was not added to the config, make sure the folder is a correct plugin "
                 "or that no plugin with the same name exists")
    return CommandResponse.fail()
