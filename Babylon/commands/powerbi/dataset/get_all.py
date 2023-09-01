import logging
import jmespath
from typing import Any, Optional

from click import command
from click import option

from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@output_to_file
@pass_powerbi_token()
@option("--workspace","workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("--filter", "filter", help="Filter response with a jmespath query")
@inject_context_with_resource({"powerbi": ['workspace']})
def get_all(context: Any, powerbi_token: str, workspace_id: str, filter: Optional[str] = None) -> CommandResponse:
    """Get a list of all powerbi datasets in the current workspace"""
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    response = oauth_request(url, powerbi_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get("value")
    if filter:
        output_data = jmespath.search(filter, output_data)
    return CommandResponse.success(output_data, verbose=True)
