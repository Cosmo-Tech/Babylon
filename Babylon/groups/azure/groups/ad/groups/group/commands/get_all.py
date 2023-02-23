import logging

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from rich.pretty import pretty_repr

from ........utils.request import oauth_request
from ........utils.response import CommandResponse
from ........utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@pass_context
@output_to_file
def get_all(ctx: Context) -> CommandResponse:
    """
    Get all AD groups from current subscription
    https://learn.microsoft.com/en-us/graph/api/group-list
    """
    access_token = ctx.find_object(AccessToken).token
    route = "https://graph.microsoft.com/v1.0/groups/"
    response = oauth_request(route, access_token, type="GET")
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
