import logging

from click import argument, command
from hvac import Client
from Babylon.utils.checkers import check_email
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command(name="user")
@pass_hvac_client
@argument("email", type=QueryType())
@argument("resource", type=QueryType())
@argument("name", type=QueryType())
def get_user_secrets(hvac_client: Client, email: str, resource: str, name: str) -> CommandResponse:
    """
    Get a secret from user scope
    """
    check_email(email)
    schema = f"{env.organization_name}/{env.tenant_id}/cache/{email}/{resource}"
    response = hvac_client.read(path=schema)
    if response is None:
        logger.info(f"{resource} not found")
        return CommandResponse.fail()

    data = response['data']
    result = None
    try:
        result = data[name]
    except Exception as exp:
        logger.info(f"{exp} not found")
        return CommandResponse.fail()
    print(result)
    return CommandResponse.success()
