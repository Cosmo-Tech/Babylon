#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import click
from Babylon.v0 import v0
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
    """CLI used for cloud interactions between CosmoTech and multiple cloud environment"""
    pass


main.add_command(v0)

if __name__ == "__main__":
    main()
