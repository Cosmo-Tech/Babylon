import logging
import jmespath

from typing import Optional
from click import command
from click import option
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file, wrapcontext
from Babylon.utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext
@output_to_file
@pass_azure_token("graph")
@option("--filter", "filter", help="Filter response with a jmespath query")
def get_all(azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all AD groups from current subscription
    https://learn.microsoft.com/en-us/graph/api/group-list
    """
    route = "https://graph.microsoft.com/v1.0/groups/"
    response = oauth_request(route, azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()["value"]
    if filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)
