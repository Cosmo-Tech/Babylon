import logging

from click import argument, command
from hvac import Client
from Babylon.utils.checkers import check_alphanum
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command(name="babylon")
@wrapcontext
@pass_hvac_client
@argument("name", type=QueryType())
@argument("value", type=QueryType())
def set_babylon(hvac_client: Client, name: str, value: str) -> CommandResponse:
    """
    Set a secret in babylon scope
    """
    check_alphanum(name)
    d = dict(secret=value)
    hvac_client.write(path=f"{env.organization_name}/{env.tenant_id}/babylon/{env.environ_id}/{name}", **d)
    logger.info("Successfully created")
    return CommandResponse.success()
