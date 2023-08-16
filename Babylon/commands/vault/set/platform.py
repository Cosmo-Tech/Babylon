import logging

from click import argument, command
from hvac import Client
from Babylon.utils.checkers import check_ascii
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_hvac_client
@argument("resource", type=QueryType())
@argument("name", type=QueryType())
@argument("value", type=QueryType())
def platform(hvac_client: Client, resource: str, name: str, value: str) -> CommandResponse:
    """
    Set a secret in platform scope
    """
    check_ascii(name)
    d = dict(secret=value)
    hvac_client.write(path=f"{env.organization_name}/{env.tenant_id}/platform/{env.environ_id}/{resource}/{name}", **d)
    logger.info("Successfully created")
    return CommandResponse.success()
