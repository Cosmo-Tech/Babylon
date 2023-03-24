import logging
from typing import Optional

from click import command
from click import option
import jmespath

from ....utils.response import CommandResponse
from ....utils.request import oauth_request
from ....utils.decorators import output_to_file
from ....utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@option("--filter", "filter", help="Filter response with a jmespath query")
@output_to_file
def get_all(azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """Get all workspace information for the given account"""
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    response = oauth_request(url=url_groups, access_token=azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get('value')
    if filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)
