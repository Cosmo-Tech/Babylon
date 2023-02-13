import logging

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import argument
from click import option

from ..........utils.request import oauth_request
from ..........utils.response import CommandResponse
from ..........utils.interactive import confirm_deletion

logger = logging.getLogger("Babylon")


@command()
@pass_context
@argument("group_id")
@argument("service_principal_id")
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
def remove(ctx: Context, group_id: str, service_principal_id: str, force_validation: bool = False) -> CommandResponse:
    """Remove a member from a group in active directory"""
    if not force_validation and not confirm_deletion("member", service_principal_id):
        return CommandResponse.fail()
    access_token = ctx.find_object(AccessToken).token
    route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/{service_principal_id}/$ref"
    logger.info(f"Deleting member {service_principal_id} from group {group_id}")
    response = oauth_request(route, access_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully removed principal {service_principal_id} from group {group_id}")
    return CommandResponse.success()
