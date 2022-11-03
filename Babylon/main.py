#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import importlib.util
import logging
import os
import pathlib
import sys

import click
import click_log
import rich.console
from rich.traceback import install

from .commands import list_commands
from .groups import list_groups
from .utils.configuration import Configuration
from .utils.decorators import prepend_doc_with_ascii
from .utils.environment import Environment
from .utils.help import HELP_CONTEXT_OVERRIDE
from .utils.help import print_cmd_help
from .utils.logging import MultiLineHandler
from .utils.working_dir import WorkingDir

logger = logging.getLogger("Babylon")
handler = MultiLineHandler(show_path=False, omit_repeated_times=False)
formatter = logging.Formatter('{message}', style='{', datefmt='%Y/%m/%d - %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

config_directory = pathlib.Path(os.environ.get('BABYLON_CONFIG_DIRECTORY', click.get_app_dir("babylon")))
conf = Configuration(logger, config_directory=config_directory)

working_directory_path = pathlib.Path(os.environ.get('BABYLON_WORKING_DIRECTORY', "."))
work_dir = WorkingDir(working_dir_path=working_directory_path, logger=logger)

env = Environment(configuration=conf, working_dir=work_dir)


@click.group(name='babylon', context_settings=HELP_CONTEXT_OVERRIDE)
@click_log.simple_verbosity_option(logger)
@click.option("--tests", "tests_mode", is_flag=True, help="Enable test mode, this mode changes output formatting.")
@click.option("-n", "--dry-run", "dry_run", is_flag=True, help="Will run commands in dry-run mode")
@click.pass_context
@click.option("-h",
              "--help",
              is_flag=True,
              callback=print_cmd_help,
              expose_value=False,
              is_eager=True,
              help="Show this message and exit.")
@prepend_doc_with_ascii
def main(ctx, tests_mode, dry_run):
    """CLI used for cloud interactions between CosmoTech and multiple cloud environment

The following environment variables are available to override the working directory or the configuration:

\b
- `BABYLON_CONFIG_DIRECTORY`: path to a folder to use as a configuration directory
- `BABYLON_WORKING_DIRECTORY`: path to a folder to use as a working directory
    """
    install(show_locals=True)
    if tests_mode:
        logger.removeHandler(handler)
        test_handler = MultiLineHandler(console=rich.console.Console(no_color=True),
                                        show_path=False,
                                        omit_repeated_times=False,
                                        show_time=False,
                                        show_level=False)
        logger.addHandler(test_handler)
    env.dry_run = dry_run
    ctx.obj = env


for plugin_name, _plugin_path in conf.get_active_plugins():
    init_path = _plugin_path / "__init__.py"

    _plugin_name = "BabylonPlugin." + plugin_name
    spec = importlib.util.spec_from_file_location(_plugin_name, init_path)
    mod = importlib.util.module_from_spec(spec)

    sys.modules[_plugin_name] = mod
    spec.loader.exec_module(mod)
    main.add_command(mod.__dict__[plugin_name])

for _group in list_groups:
    main.add_command(_group)

for _command in list_commands:
    main.add_command(_command)

if __name__ == "__main__":
    main()
