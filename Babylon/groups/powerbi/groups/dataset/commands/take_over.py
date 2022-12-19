import logging
from typing import Optional

from click import command
from click import pass_context
from click import Context
from click import argument
from click import option
import requests

from ......utils.decorators import require_deployment_key
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
@argument("dataset_id")
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
def take_over(ctx: Context,
              powerbi_workspace_id: str,
              dataset_id: str,
              workspace_id: Optional[str] = None) -> CommandResponse:
    """Get a list of all powerbi datasets in the current workspace"""
    workspace_id = workspace_id or powerbi_workspace_id
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/Default.TakeOver"
    try:
        response = requests.post(url=urls_reports, headers=header)
    except Exception as e:
        logger.error(f"Request failed {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    if response.status_code != 200:
        logger.error(f"Request failed: {response.text}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    logger.info(f"Successfully took ownership of dataset {dataset_id}")
    return CommandResponse()
