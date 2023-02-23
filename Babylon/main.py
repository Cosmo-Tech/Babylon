#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import importlib.util
import logging
import os
import sys

import click
import click_log
from rich.highlighter import NullHighlighter
from rich.traceback import install

from .commands import list_commands
from .groups import list_groups
from .utils.decorators import prepend_doc_with_ascii
from .utils.dry_run import display_dry_run
from .utils.environment import Environment
from .utils.interactive import INTERACTIVE_ARG_VALUE
from .utils.interactive import interactive_run
from .utils.logging import MultiLineHandler
from .version import VERSION

logger = logging.getLogger("Babylon")
handler = MultiLineHandler(show_path=False, omit_repeated_times=False)
formatter = logging.Formatter('{message}', style='{', datefmt='%Y/%m/%d - %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

env = Environment()


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(VERSION)
    ctx.exit()


@click.group(name='babylon', invoke_without_command=False)
@click_log.simple_verbosity_option(logger)
@click.option("--bare",
              "--raw",
              "--tests",
              "tests_mode",
              is_flag=True,
              help="Enable test mode, this mode changes output formatting.")
@click.option("-n",
              "--dry-run",
              "dry_run",
              callback=display_dry_run,
              is_flag=True,
              expose_value=False,
              is_eager=True,
              help="Will run commands in dry-run mode.")
@click.option('--version',
              is_flag=True,
              callback=print_version,
              expose_value=False,
              is_eager=True,
              help="Print version number and return.")
@click.option(INTERACTIVE_ARG_VALUE,
              "interactive",
              is_flag=True,
              hidden=True,
              help="Start an interactive session after command run.")
@prepend_doc_with_ascii
def main(tests_mode, interactive):
    """CLI used for cloud interactions between CosmoTech and multiple cloud environment

The following environment variables are available to override the working directory or the configuration:

\b
- `BABYLON_CONFIG_DIRECTORY`: path to a folder to use as a configuration directory
- `BABYLON_WORKING_DIRECTORY`: path to a folder to use as a working directory
    """
    if tests_mode:
        os.environ.setdefault("NO_COLOR", "True")
        logger.removeHandler(handler)
        test_handler = MultiLineHandler(highlighter=NullHighlighter(),
                                        show_path=False,
                                        omit_repeated_times=False,
                                        show_time=False,
                                        show_level=False)
        logger.addHandler(test_handler)
    else:
        install(width=os.get_terminal_size().columns)


main.result_callback()(interactive_run)

for plugin_name, _plugin_path in env.configuration.get_active_plugins():
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
