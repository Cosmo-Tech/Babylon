import logging

from typing import Any
from click import command
from click import argument
from click import option
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource, output_to_file
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@output_to_file
@pass_powerbi_token()
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("-s", "--select", "select", is_flag=True, default=True, help="Select this new report in configuration")
@argument("report_id", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def get(
    context: Any,
    powerbi_token: str,
    report_id: str,
    workspace_id: str,
    select: str,
) -> CommandResponse:
    """
    Get info from a powerbi report of a workspace
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
    response = oauth_request(urls_reports, powerbi_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    return CommandResponse.success(output_data, verbose=True)
