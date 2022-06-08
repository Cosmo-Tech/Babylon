#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import click
from Babylon.commands import command_groups
import logging
import click_log
import sys

logger = logging.getLogger("Babylon")
handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@click.group()
@click_log.simple_verbosity_option(logger)
def main():
    pass


for c in command_groups:
    main.add_command(c)

if __name__ == "__main__":
    main()
