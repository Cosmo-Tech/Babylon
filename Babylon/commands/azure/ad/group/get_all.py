import logging

from click import command
from rich.pretty import pretty_repr

from .....utils.request import oauth_request
from .....utils.response import CommandResponse
from .....utils.decorators import output_to_file
from .....utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token()
@output_to_file
def get_all(azure_token: str) -> CommandResponse:
    """
    Get all AD groups from current subscription
    https://learn.microsoft.com/en-us/graph/api/group-list
    """
    route = "https://graph.microsoft.com/v1.0/groups/"
    response = oauth_request(route, azure_token, type="GET")
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
