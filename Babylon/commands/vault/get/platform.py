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


@command()
@wrapcontext()
@pass_hvac_client
@argument("resource", type=QueryType())
@argument("name", type=QueryType())
def platform(
    hvac_client: Client,
    resource: str,
    name: str,
) -> CommandResponse:
    """
    Get a secret from platform scope
    """
    check_alphanum(name)
    schema = f"{env.organization_name}/{env.tenant_id}/platform/{env.environ_id}/{resource}/{name}"
    response = hvac_client.read(path=schema)
    if not response:
        logger.info("Secret not found")
        return CommandResponse.fail()
    print(response['data']['secret'])
    return CommandResponse.success()
