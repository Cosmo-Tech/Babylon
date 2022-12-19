import logging

from click import argument
from click import command

from ......utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@argument("deploy", nargs=1, type=str)
def create(deploy: str):
    """Create a new deployment file DEPLOY.yaml and open editor to edit it"""
    config = Environment().configuration
    config.create_deploy(deploy)
