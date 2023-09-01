import logging

from click import command, option
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("graph")
@option("--gi", "--group-id", "group_id", type=QueryType(), required=True)
@option("--pi", "--object-id", "object_id", type=QueryType(), required=True)
def add(
    azure_token: str,
    group_id: str,
    object_id: str,
) -> CommandResponse:
    """
    Add a member in a group in active directory
    https://learn.microsoft.com/en-us/graph/api/group-post-members
    """
    route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
    details = {"@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{object_id}"}
    response = oauth_request(route, azure_token, type="POST", json=details)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully added principal {object_id} to group {group_id}")
    return CommandResponse.success()
