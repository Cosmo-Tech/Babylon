import logging
from typing import Optional

from click import command
from click import option
import jmespath

from .....utils.request import oauth_request
from .....utils.response import CommandResponse
from .....utils.decorators import output_to_file
from .....utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("graph")
@option("--filter", "filter", help="Filter response with a jmespath query")
@output_to_file
def get_all(azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all apps registered in active directory
    https://learn.microsoft.com/en-us/graph/api/application-list
    """
    route = "https://graph.microsoft.com/v1.0/applications"
    response = oauth_request(route, azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()["value"]
    if filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)
