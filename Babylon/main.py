#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import importlib.util
import logging
import sys
import click_log
import click

from click import option
from click import group
from click import echo
from rich.logging import RichHandler
from Babylon.commands import list_groups
from Babylon.utils.decorators import prepend_doc_with_ascii
from Babylon.utils.dry_run import display_dry_run
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import INTERACTIVE_ARG_VALUE
from Babylon.utils.interactive import interactive_run
from Babylon.version import VERSION

logger = logging.getLogger("Babylon")
env = Environment()


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    echo(VERSION)
    ctx.exit()


@group(name='babylon', invoke_without_command=False)
@click_log.simple_verbosity_option(logger)
@option("--bare",
        "--raw",
        "--tests",
        "tests_mode",
        is_flag=True,
        help="Enable test mode, this mode changes output formatting.")
@option("-n",
        "--dry-run",
        "dry_run",
        callback=display_dry_run,
        is_flag=True,
        expose_value=False,
        is_eager=True,
        help="Will run commands in dry-run mode.")
@option('--version',
        is_flag=True,
        callback=print_version,
        expose_value=False,
        is_eager=True,
        help="Print version number and return.")
@option(INTERACTIVE_ARG_VALUE,
        "interactive",
        is_flag=True,
        hidden=True,
        help="Start an interactive session after command run.")
@prepend_doc_with_ascii
def main(tests_mode, interactive):
    """CLI used for cloud interactions between CosmoTech and multiple cloud environment

The following environment variables are required:

\b
- BABYLON_SERVICE: Vault Service URI
- BABYLON_TOKEN: Access Token Vault Service
- BABYLON_ORG_NAME: Organization Name
    """
    if not tests_mode:
        sys.tracebacklimit = 0
        logging.basicConfig(
            format="%(message)s",
            datefmt="[%Y/%m/%d - %X]",
            handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=click, omit_repeated_times=False)])


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

if __name__ == "__main__":
    main()
