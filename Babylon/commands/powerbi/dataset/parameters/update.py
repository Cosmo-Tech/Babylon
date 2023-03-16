import logging
from typing import Optional

from click import command
from click import argument
from click import option

from .....utils.decorators import require_deployment_key
from .....utils.request import oauth_request
from .....utils.response import CommandResponse
from .....utils.typing import QueryType
from .....utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@require_deployment_key("powerbi_workspace_id", required=False)
@argument("dataset_id", type=QueryType())
@option("-p", "--parameter", "params", type=(QueryType(), QueryType()), multiple=True, required=True)
@option("-w", "--workspace", "workspace_id", type=QueryType(), help="PowerBI workspace ID")
def update(azure_token: str,
           powerbi_workspace_id: str,
           dataset_id: str,
           params: list[tuple[str, str]],
           workspace_id: Optional[str] = None) -> CommandResponse:
    """Update parameters of a given dataset"""
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    # Preparing parameter data
    details = {"updateDetails": [{"name": param[0], "newValue": param[1]} for param in params]}
    update_url = (f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
                  f"/datasets/{dataset_id}/Default.UpdateParameters")
    response = oauth_request(update_url, azure_token, json=details, type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully updated dataset {dataset_id} parameters")
    return CommandResponse.success()