#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import logging

import click
import click_log

from .commands import list_commands
from .groups import list_groups
from .utils.configuration import Configuration
from .utils.solution import Solution
from .utils.logging import MultiLineHandler
from .v0 import v0

logger = logging.getLogger("Babylon")
handler = MultiLineHandler()
formatter = logging.Formatter('{levelname:>8} - {asctime} | {message}', style='{', datefmt='%Y/%m/%d - %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


@click.group()
@click_log.simple_verbosity_option(logger)
@click.option("-s", "--solution", "solution_path", default=".",
              help="Path to a local solution (folder/zip) used to run the commands. "
                   "Defaults to current folder")
@click.option("--tests", "tests_mode", is_flag=True,
              help="Is babylon running in test mode ? This mode change output formatting.")
@click.option("--dry_run", "dry_run", is_flag=True,
              help="Will run commands in dry-run mode")
@click.pass_context
def main(ctx, solution_path, tests_mode, dry_run):
    """CLI used for cloud interactions between CosmoTech and multiple cloud environment"""
    if tests_mode:
        handler.setFormatter(logging.Formatter('{message}', style='{'))
    conf = Configuration(logger)
    solution = Solution(solution_path, logger, conf, dry_run)
    ctx.obj = solution


main.add_command(v0)
for _group in list_groups:
    main.add_command(_group)

for _command in list_commands:
    main.add_command(_command)

if __name__ == "__main__":
    main()
