import logging
import pathlib
from typing import Optional

import click
from click import group
from click import option
from click import pass_context

from Babylon.utils import BABYLON_PATH
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import pass_environment
from .commands import list_commands
from .groups import list_groups

logger = logging.getLogger("Babylon")


@group()
@pass_environment
@pass_context
@option("-p", "--plugin", "plugin", type=str, required=False)
def dev_tools(ctx: click.Context, environment: Environment, plugin: Optional[str] = None):
    """Plugin used to simplify some development operations"""
    base_path = BABYLON_PATH
    if plugin:
        config = environment.configuration
        if plugin not in list(config.get_available_plugin()):
            logger.error(f"Plugin `{plugin}` does not exists.")
            raise click.Abort()
        else:
            for _p in config.plugins:
                if _p['name'] == plugin:
                    base_path = pathlib.Path(_p['path'])
                    break
    ctx.obj = base_path


for _command in list_commands:
    dev_tools.add_command(_command)

for _group in list_groups:
    dev_tools.add_command(_group)
