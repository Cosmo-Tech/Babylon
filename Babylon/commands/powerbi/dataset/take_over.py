import logging
from typing import Any

from click import command
from click import argument
from click import option

from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@pass_powerbi_token()
@option("-w", "--workspace", "workspace_id", type=QueryType(), help="PowerBI workspace ID")
@argument("dataset_id", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def take_over(
    context: Any,
    powerbi_token: str,
    workspace_id: str,
    dataset_id: str,
) -> CommandResponse:
    """
    Take ownership of a powerbi dataset in the current workspace
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/Default.TakeOver"
    response = oauth_request(url, powerbi_token, type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully took ownership of dataset {dataset_id}")
    return CommandResponse.success()
