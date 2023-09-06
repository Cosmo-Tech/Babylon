import logging

from typing import Any, Optional
from click import command
from click import argument
from click import option
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@option("--parameter", "params", type=(QueryType(), QueryType()), multiple=True, required=True, help="Report parameter")
@option("--workspace", "workspace_id", type=QueryType(), help="PowerBI workspace ID")
@argument("dataset_id", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def update(context: Any,
           powerbi_token: str,
           dataset_id: str,
           params: list[tuple[str, str]],
           workspace_id: Optional[str] = None) -> CommandResponse:
    """
    Update parameters of a given dataset
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    # Preparing parameter data
    details = {"updateDetails": [{"name": param[0], "newValue": param[1]} for param in params]}
    update_url = (f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
                  f"/datasets/{dataset_id}/Default.UpdateParameters")
    response = oauth_request(update_url, powerbi_token, json=details, type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info("Successfully updated")
    return CommandResponse.success()
