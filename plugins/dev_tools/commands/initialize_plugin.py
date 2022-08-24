import logging
import os
import pathlib
import shutil

import click

from Babylon.utils import TEMPLATE_FOLDER_PATH
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import pass_environment
from Babylon.utils.string import is_valid_command_name

logger = logging.getLogger("Babylon")


@click.command()
@click.argument("plugin_folder", type=click.Path(file_okay=False,
                                                 dir_okay=True,
                                                 readable=True,
                                                 writable=True,
                                                 path_type=pathlib.Path))
@click.argument("plugin_name")
@click.option("-a", "--add", "add", is_flag=True, help="Add the created plugin to the config.")
@pass_environment
def initialize_plugin(environment: Environment, plugin_name: str, plugin_folder: pathlib.Path, add: bool = False):
    """Will initialize PLUGIN_NAME in PLUGIN_FOLDER"""

    plugin_name = plugin_name.replace("-", "_")
    if not is_valid_command_name(plugin_name):
        logger.error(f"`{plugin_name}` contains illegal characters")
        return

    plugin_template = TEMPLATE_FOLDER_PATH / "plugin_template"

    if plugin_folder.exists():
        logger.error(f"{plugin_folder.absolute()} already exists")
        return

    if add:
        if plugin_name in environment.configuration.get_available_plugin():
            logger.error(f"Plugin `{plugin_name}` already exists in the config.")
            return

    os.makedirs(str(plugin_folder), exist_ok=True)

    logger.info(f"Creating plugin folder tree at {plugin_folder.absolute()}")
    shutil.copytree(plugin_template, plugin_folder, dirs_exist_ok=True)

    for root, _, _files in os.walk(str(plugin_folder)):

        for _f_name in _files:
            _f_path = pathlib.Path(root) / _f_name
            _f_content = []
            with open(_f_path) as _f:
                for _line in _f:
                    _f_content.append(_line.replace('plugin_template', plugin_name))
            with open(_f_path, "w") as _f:
                _f.write("".join(_f_content))

    logger.info(f"Plugin {plugin_name} is ready")
    if add:
        config.add_plugin(plugin_folder)
        logger.info(f"Plugin {plugin_name} was added to the configuration.")
    logger.info(f"Use `babylon config plugin` to see how to interact with it")
    logger.info(f"Use `babylon dev --plugin {plugin_name}` to use dev commands on your plugin")
