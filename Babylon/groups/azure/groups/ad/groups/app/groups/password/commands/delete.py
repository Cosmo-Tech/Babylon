import logging

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import option
from click import argument

from ..........utils.interactive import confirm_deletion
from ..........utils.request import oauth_request
from ..........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("app_id")
@option("-k", "--key", "key_id", help="Password Key ID", required=True)
@option("-f", "--force", "force_validation", is_flag=True, help="Don't ask for validation before delete")
def delete(ctx: Context, app_id: str, key_id: str, force_validation: bool = False) -> CommandResponse:
    """
    Delete a password for an app registration in active directory
    https://learn.microsoft.com/en-us/graph/api/application-delete
    """
    if not force_validation and not confirm_deletion("secret", key_id):
        return CommandResponse.fail()
    access_token = ctx.find_object(AccessToken).token
    logger.info(f"Deleting secret {key_id} of app registration {app_id}")
    route = f"https://graph.microsoft.com/v1.0/applications/{app_id}/removePassword"
    response = oauth_request(route, access_token, type="POST", json={"keyId": key_id})
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully deleted secret {key_id} of app registration {app_id}")
    return CommandResponse.success()