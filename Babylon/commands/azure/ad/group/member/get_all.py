import logging

from click import command
from click import argument
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@output_to_file
@pass_azure_token("graph")
@argument("group_id", type=QueryType())
def get_all(azure_token: str, group_id: str) -> CommandResponse:
    """
    Get members of a group in active directory
    https://learn.microsoft.com/en-us/graph/api/group-post-members
    """
    route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/"
    response = oauth_request(route, azure_token, type="GET")
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    return CommandResponse.success(output_data, verbose=True)
