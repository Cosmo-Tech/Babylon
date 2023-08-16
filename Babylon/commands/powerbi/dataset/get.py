import logging
from typing import Any

from click import command
from click import option
from click import argument

from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@pass_powerbi_token()
@argument("dataset_id", type=QueryType())
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@output_to_file
@inject_context_with_resource({"powerbi": ['workspace']})
def get(
    context: Any,
    powerbi_token: str,
    workspace_id: str,
    dataset_id: str,
) -> CommandResponse:
    """
    Get a powerbi dataset in the current workspace
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
    response = oauth_request(url, powerbi_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    return CommandResponse.success(output_data, verbose=True)
