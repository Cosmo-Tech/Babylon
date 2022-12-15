import logging
import pathlib
from typing import Optional

import click
from click import argument
from click import command

from ......utils.environment import Environment
from ......utils.interactive import select_from_list

logger = logging.getLogger("Babylon")


@command()
@argument("deployment", required=False, type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
def select(deployment: Optional[pathlib.Path] = None):
    """Change current selected deployment

    if not argument is passed will run in interactive mode"""
    config = Environment().configuration
    if deployment:
        if config.set_deploy(deployment):
            logger.info("Configuration successfully updated")
        else:
            logger.error(f"Configuration was not updated. {deployment} is not a valid deployment file.")
    else:
        logger.debug("Interactive change of deploy:")
        available_deploys = list(config.list_deploys())
        new_deploy = select_from_list(available_deploys, config.deploy)
        if new_deploy:
            config.set_deploy(new_deploy)
            logger.debug("Configuration successfully updated")
        else:
            logger.error("Issue while selecting new deployment configuration")
