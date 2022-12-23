import logging

from click import argument
from click import command

from ......utils.environment import Environment
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("deploy", nargs=1, type=str)
def create(deploy: str) -> CommandResponse:
    """Create a new deployment file DEPLOY.yaml and open editor to edit it"""
    config = Environment().configuration
    if not config.create_deploy(deploy):
        return CommandResponse.fail()
    return CommandResponse()
