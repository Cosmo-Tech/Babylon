import logging

from click import argument
from click import command

from ......utils.configuration import Configuration
from ......utils.decorators import pass_config

logger = logging.getLogger("Babylon")


@command()
@pass_config
@argument("deploy", nargs=1, type=str)
def create(config: Configuration, deploy: str):
    """Create a new deployment file DEPLOY.yaml and open editor to edit it"""
    config.create_deploy(deploy)
