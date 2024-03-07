import logging
from click import argument, command
from hvac import Client
from Babylon.utils.checkers import check_ascii, check_email
from Babylon.utils.clients import pass_hvac_client
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command(name="user")
@pass_hvac_client
@argument("email", type=str)
@argument("resource", type=str)
@argument("name", type=str)
@argument("value", type=str)
def set_user_secrets(
    hvac_client: Client,
    email: str,
    resource: str,
    name: str,
    value: str,
) -> CommandResponse:
    """
    Set a secret in user scope
    """
    check_email(email)
    check_ascii(resource)
    d = dict()
    d.update({f'{name}': value})
    schema = f"{env.organization_name}/{env.tenant_id}/users/{email}/{resource}"
    hvac_client.write(path=schema, **d)
    logger.info("[vault] successfully created user secret")
    return CommandResponse.success()
