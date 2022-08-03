#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import logging

import click
import click_log

from .groups import list_groups
from .commands import list_commands
from .utils.environment import Environment
from .utils.logging import MultiLineHandler
from .v0 import v0

logger = logging.getLogger("Babylon")
handler = MultiLineHandler()
formatter = logging.Formatter('{levelname:>8} - {asctime} | {message}', style='{', datefmt='%Y/%m/%d - %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


@click.group()
@click_log.simple_verbosity_option(logger)
@click.option("-e", "--environment", "environment_path", default=".",
              help="Path to a local environment (folder/zip) used to run the commands. "
                   "Defaults to run folder")
@click.option("-t", "--template", "template_path", default=None,
              help="Path to an environment template. "
                   "Defaults to <BabylonInstall>/Babylon/utils/EnvironmentTemplate")
@click.option("--dry_run", "dry_run", is_flag=True,
              help="Will run commands in dry-run mode")
@click.pass_context
def main(ctx, environment_path, template_path, dry_run):
    """CLI used for cloud interactions between CosmoTech and multiple cloud environment"""
    env = Environment(environment_path, logger, template_path, dry_run)
    ctx.obj = env


main.add_command(v0)
for _group in list_groups:
    main.add_command(_group)

for _command in list_commands:
    main.add_command(_command)

if __name__ == "__main__":
    main()
