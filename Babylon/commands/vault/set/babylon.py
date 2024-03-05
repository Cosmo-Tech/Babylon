import logging

from click import argument, command
from hvac import Client
from Babylon.utils.checkers import check_ascii
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command(name="babylon")
@injectcontext()
@pass_hvac_client
@argument("name", type=str)
@argument("value", type=str)
def set_babylon(hvac_client: Client, name: str, value: str) -> CommandResponse:
    """
    Set a secret in babylon scope
    """
    check_ascii(name)
    d = dict(secret=value)
    hvac_client.write(path=f"{env.organization_name}/{env.tenant_id}/babylon/{env.environ_id}/{name}", **d)
    logger.info("Successfully created")
    return CommandResponse.success()
