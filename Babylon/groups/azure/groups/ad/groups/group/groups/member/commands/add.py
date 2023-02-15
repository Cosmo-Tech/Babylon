import logging

from click import command
from click import argument

from ..........utils.request import oauth_request
from ..........utils.response import CommandResponse
from ..........utils.typing import QueryType
from ..........utils.credentials import get_azure_token

logger = logging.getLogger("Babylon")


@command()
@argument("group_id", type=QueryType())
@argument("service_principal_id", type=QueryType())
def add(group_id: str, service_principal_id: str) -> CommandResponse:
    """
    Add a member in a group in active directory
    https://learn.microsoft.com/en-us/graph/api/group-post-members
    """
    route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
    details = {"@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{service_principal_id}"}
    response = oauth_request(route, get_azure_token("graph"), type="POST", json=details)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully added principal {service_principal_id} to group {group_id}")
    return CommandResponse.success()
