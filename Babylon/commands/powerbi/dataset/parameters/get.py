import logging

from typing import Any, Optional
from click import command
from click import argument
from click import option
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.request import oauth_request
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@output_to_file
@pass_powerbi_token()
@option("--workspace", "workspace_id", type=QueryType(), help="PowerBI workspace ID")
@argument("dataset_id", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def get(context: Any, powerbi_token: str, dataset_id: str, workspace_id: Optional[str] = None) -> CommandResponse:
    """
    Get parameters of a given dataset
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    update_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/parameters"
    response = oauth_request(update_url, powerbi_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get("value")
    return CommandResponse.success(output_data, verbose=True)
