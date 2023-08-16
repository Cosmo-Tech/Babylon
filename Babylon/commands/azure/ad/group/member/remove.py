import logging

from click import command
from click import option
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_azure_token("graph")
@option("--gi", "--group-id", "group_id", type=QueryType(), required=True, help="Group Id Azure Directory")
@option("--pi", "--principal-id", "principal_id", type=QueryType(), required=True, help="Principal Id Azure Directory")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
def remove(azure_token: str, group_id: str, principal_id: str, force_validation: bool = False) -> CommandResponse:
    """
    Remove a member from a group in active directory
    """
    if not force_validation and not confirm_deletion("member", principal_id):
        return CommandResponse.fail()
    route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/{principal_id}/$ref"
    logger.info(f"Deleting member {principal_id} from group {group_id}")
    response = oauth_request(route, azure_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully removed principal {principal_id} from group {group_id}")
    return CommandResponse.success()
