import logging
import jmespath

from typing import Optional
from click import command
from click import option
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import output_to_file, wrapcontext
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext
@output_to_file
@pass_powerbi_token()
@option("--filter", "filter", help="Filter response with a jmespath query")
def get_all(powerbi_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all workspace information for the given account
    """
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    response = oauth_request(url=url_groups, access_token=powerbi_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get('value')
    if len(output_data) and filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)
