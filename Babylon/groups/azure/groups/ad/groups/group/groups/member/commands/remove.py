import logging

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import argument

from ..........utils.request import oauth_request
from ..........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("group_id")
@argument("service_principal_id")
def remove(ctx: Context, group_id: str, service_principal_id: str) -> CommandResponse:
    """Remove a member from a group in active directory"""
    access_token = ctx.find_object(AccessToken).token
    route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/{service_principal_id}/$ref"
    response = oauth_request(route, access_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully removed principal {service_principal_id} from group {group_id}")
    return CommandResponse.success()
