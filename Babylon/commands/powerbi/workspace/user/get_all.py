import logging
from typing import Optional

from click import command
from click import option
import jmespath

from .....utils.decorators import output_to_file
from .....utils.typing import QueryType
from .....utils.response import CommandResponse
from .....utils.request import oauth_request
from .....utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@option("-w", "--workspace", "workspace_id", type=QueryType(), default="%deploy%powerbi_workspace_id")
@option("--filter", "filter", help="Filter response with a jmespath query")
@output_to_file
def get_all(azure_token: str, workspace_id: str, filter: Optional[str] = None) -> CommandResponse:
    """List all exisiting users in the power bi workspace"""
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    url_users = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users'
    response = oauth_request(url_users, azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get('value')
    if filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)
