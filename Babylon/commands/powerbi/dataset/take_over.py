import logging
from typing import Optional

from click import command
from click import argument
from click import option

from ....utils.decorators import require_deployment_key
from ....utils.response import CommandResponse
from ....utils.request import oauth_request
from ....utils.typing import QueryType
from ....utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@require_deployment_key("powerbi_workspace_id", required=False)
@argument("dataset_id")
@option("-w", "--workspace", "workspace_id", type=QueryType(), help="PowerBI workspace ID")
def take_over(azure_token: str,
              powerbi_workspace_id: str,
              dataset_id: str,
              workspace_id: Optional[str] = None) -> CommandResponse:
    """Take ownership of a powerbi dataset in the current workspace"""
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/Default.TakeOver"
    response = oauth_request(url, azure_token, type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully took ownership of dataset {dataset_id}")
    return CommandResponse.success()
