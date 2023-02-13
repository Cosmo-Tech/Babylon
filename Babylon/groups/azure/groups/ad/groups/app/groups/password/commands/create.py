import logging
from typing import Optional

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import option
from click import argument
from rich.pretty import pretty_repr

from ..........utils.request import oauth_request
from ..........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("app_id")
@option("-n", "--name", "password_name", help="Password display name")
def create(ctx: Context, app_id: str, password_name: Optional[str] = None) -> CommandResponse:
    """
    Register a password or secret to an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-addpassword
    """
    access_token = ctx.find_object(AccessToken).token
    route = f"https://graph.microsoft.com/v1.0/applications/{app_id}/addPassword"
    details = {"passwordCredential": {"displayName": password_name or f"secret_{app_id}"}}
    response = oauth_request(route, access_token, type="POST", json=details)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
