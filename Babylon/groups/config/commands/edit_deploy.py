import logging
from typing import Optional

from click import argument
from click import command

from ....utils.configuration import Configuration
from ....utils.decorators import pass_config

logger = logging.getLogger("Babylon")


@command()
@pass_config
@argument("deployment", required=False, type=str)
def edit_deploy(config: Configuration, deployment: Optional[str] = None):
    """Open editor to edit variables in given deployment

    will open default deployment if no argument is passed"""
    if deployment:
        config.edit_deploy(deployment)
    else:
        config.edit_deploy(config.deploy)
