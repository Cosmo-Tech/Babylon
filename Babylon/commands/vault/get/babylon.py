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


@command(name="babylon")
@wrapcontext()
@pass_hvac_client
@argument("name", type=QueryType())
def get_babylon(
    hvac_client: Client,
    name: str,
) -> CommandResponse:
    """
    Get a secret from babylon scope
    """
    check_ascii(name)
    schema = f"{env.organization_name}/{env.tenant_id}/babylon/{env.environ_id}/{name}"
    response = hvac_client.read(path=schema)
    if not response:
        logger.info("Secret not found")
        return CommandResponse.fail()
    print(response['data']['secret'])
    return CommandResponse.success()
