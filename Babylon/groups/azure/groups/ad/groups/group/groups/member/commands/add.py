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
def add(ctx: Context, group_id: str, service_principal_id: str) -> CommandResponse:
    """
    Add a member in a group in active directory
    https://learn.microsoft.com/en-us/graph/api/group-post-members
    """
    access_token = ctx.find_object(AccessToken).token
    route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
    details = {"@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{service_principal_id}"}
    response = oauth_request(route, access_token, type="POST", json=details)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully added principal {service_principal_id} to group {group_id}")
    return CommandResponse.success()
