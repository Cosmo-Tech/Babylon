import logging
import pathlib
from typing import Optional

import click
from click import argument
from click import command

from ......utils.configuration import Configuration
from ......utils.decorators import pass_config

logger = logging.getLogger("Babylon")


@command()
@pass_config
@argument("deployment",
          required=False,
          type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
def edit(config: Configuration, deployment: Optional[pathlib.Path] = None):
    """Open editor to edit variables in given deployment

    will open default deployment if no argument is passed"""
    if deployment:
        config.edit_deploy(deployment)
    else:
        config.edit_deploy(config.get_deploy_path())
