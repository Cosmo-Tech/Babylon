#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import click
from .v0 import v0
from .groups import command_groups
import click_log
import logging
from .utils.logging import MultiLineHandler
from .utils.environment import Environment

logger = logging.getLogger("Babylon")
handler = MultiLineHandler()
formatter = logging.Formatter('{levelname:8}| {message}', style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)


@click.group()
@click_log.simple_verbosity_option(logger)
@click.option("-e", "--environment", "environment_path", default=".")
@click.option("-t", "--template", "template_path", default=None)
@click.pass_context
def main(ctx, environment_path, template_path):
    """CLI used for cloud interactions between CosmoTech and multiple cloud environment"""
    env = Environment(environment_path, logger, template_path)
    ctx.obj = env


main.add_command(v0)
for _group in command_groups:
    main.add_command(_group)

if __name__ == "__main__":
    main()
