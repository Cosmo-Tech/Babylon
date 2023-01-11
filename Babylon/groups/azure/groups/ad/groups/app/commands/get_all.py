import logging

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from rich.pretty import pretty_repr

from ........utils.request import oauth_request
from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
def get_all(ctx: Context) -> CommandResponse:
    """
    Get all apps registered in active directory
    https://learn.microsoft.com/en-us/graph/api/application-list
    """
    access_token = ctx.find_object(AccessToken).token
    route = "https://graph.microsoft.com/v1.0/applications"
    response = oauth_request(route, access_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
