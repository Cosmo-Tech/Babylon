import logging
import pathlib
from typing import Optional

import click
from click import argument
from click import command

from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("deployment",
          required=False,
          type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path))
def edit(deployment: Optional[pathlib.Path] = None) -> CommandResponse:
    """Open editor to edit variables in given deployment

    will open default deployment if no argument is passed"""
    config = Environment().configuration
    if deployment:
        config.edit_deploy(deployment)
    else:
        config.edit_deploy(config.get_deploy_path())
    return CommandResponse.success()
