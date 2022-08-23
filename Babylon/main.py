#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import importlib.util
import logging

import click
import click_log
import sys

from .commands import list_commands
from .groups import list_groups
from .utils.configuration import Configuration
from .utils.logging import MultiLineHandler
from .utils.solution import Solution
from .v0 import v0

logger = logging.getLogger("Babylon")
handler = MultiLineHandler()
formatter = logging.Formatter('{levelname:>8} - {asctime} | {message}', style='{', datefmt='%Y/%m/%d - %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

conf = Configuration(logger)


@click.group()
@click_log.simple_verbosity_option(logger)
@click.option("-s", "--solution", "solution_path", default=".",
              help="Path to a local solution (folder/zip) used to run the commands. "
                   "Defaults to current folder")
@click.option("--tests", "tests_mode", is_flag=True,
              help="Enable test mode, this mode changes output formatting.")
@click.option("-n", "--dry-run", "dry_run", is_flag=True,
              help="Will run commands in dry-run mode")
@click.option("--platform", "platform_override", help="Path to a yaml to override the platform configuration",
              type=click.Path(exists=True, dir_okay=False, readable=True, file_okay=True))
@click.option("--deploy", "deploy_override", help="Path to a yaml to override the deploy configuration",
              type=click.Path(exists=True, dir_okay=False, readable=True, file_okay=True))
@click.option("--config", "config_override", help="Path to a dir to use as an override for the system config",
              type=click.Path(dir_okay=True, readable=True, file_okay=False, path_type=pathlib.Path))
@click.pass_context
def main(ctx, solution_path, tests_mode, dry_run, platform_override=None, deploy_override=None, config_override=None):
    """CLI used for cloud interactions between CosmoTech and multiple cloud environment"""
    if tests_mode:
        handler.setFormatter(logging.Formatter('{message}', style='{'))
    if config_override:
        conf = Configuration(logger=logger, config_directory=config_override)
    solution = Solution(solution_path, logger, conf, dry_run)
    solution.config.override(override_deploy=deploy_override, override_platform=platform_override)
    ctx.obj = solution


for plugin_name, _plugin_path in conf.get_active_plugins():
    init_path = _plugin_path / "__init__.py"

    _plugin_name = "BabylonPlugin."+plugin_name
    spec = importlib.util.spec_from_file_location(_plugin_name, init_path)
    mod = importlib.util.module_from_spec(spec)

    sys.modules[_plugin_name] = mod
    spec.loader.exec_module(mod)
    main.add_command(mod.__dict__[plugin_name])

main.add_command(v0)
for _group in list_groups:
    main.add_command(_group)

for _command in list_commands:
    main.add_command(_command)

if __name__ == "__main__":
    main()
