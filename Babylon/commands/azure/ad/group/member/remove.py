import logging

from click import command
from click import option
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("graph")
@option("--gi", "--group-id", "group_id", type=QueryType(), required=True)
@option("--pi", "--object-id", "object_id", type=QueryType(), required=True)
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
def remove(azure_token: str, group_id: str, object_id: str, force_validation: bool = False) -> CommandResponse:
    """
    Remove a member from a group in active directory
    """
    if not force_validation and not confirm_deletion("member", object_id):
        return CommandResponse.fail()
    route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/{object_id}/$ref"
    logger.info(f"Deleting member {object_id} from group {group_id}")
    response = oauth_request(route, azure_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully removed principal {object_id} from group {group_id}")
    return CommandResponse.success()
