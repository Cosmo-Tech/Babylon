import logging

from click import command
from click import argument

from ..........utils.request import oauth_request
from ..........utils.response import CommandResponse
from ..........utils.typing import QueryType
from ..........utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("graph")
@argument("group_id", type=QueryType())
@argument("service_principal_id", type=QueryType())
def add(azure_token: str, group_id: str, service_principal_id: str) -> CommandResponse:
    """
    Add a member in a group in active directory
    https://learn.microsoft.com/en-us/graph/api/group-post-members
    """
    route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
    details = {"@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{service_principal_id}"}
    response = oauth_request(route, azure_token, type="POST", json=details)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully added principal {service_principal_id} to group {group_id}")
    return CommandResponse.success()
