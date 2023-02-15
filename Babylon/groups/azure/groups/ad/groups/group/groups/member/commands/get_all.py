import logging

from click import command
from click import argument
from rich.pretty import pretty_repr

from ..........utils.request import oauth_request
from ..........utils.response import CommandResponse
from ..........utils.decorators import output_to_file
from ..........utils.credentials import get_azure_token

logger = logging.getLogger("Babylon")


@command()
@argument("group_id")
@output_to_file
def get_all(group_id: str) -> CommandResponse:
    """
    Get members of a group in active directory
    https://learn.microsoft.com/en-us/graph/api/group-post-members
    """
    route = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/"
    response = oauth_request(route, get_azure_token("graph"), type="GET")
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success()
