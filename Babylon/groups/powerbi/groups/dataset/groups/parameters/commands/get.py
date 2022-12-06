import logging
import requests
from typing import Optional

from click import command
from click import argument
from click import pass_context
from click import Context
from click import option

from ........utils.decorators import require_deployment_key
from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
@argument("dataset_id")
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
def get(ctx: Context,
        powerbi_workspace_id: str,
        dataset_id: str,
        workspace_id: Optional[str] = None) -> CommandResponse:
    """Get parameters of a given dataset"""
    access_token = ctx.obj.token
    workspace_id = workspace_id or powerbi_workspace_id
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    update_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/parameters"
    try:
        response = requests.get(url=update_url, headers=header)
    except Exception as e:
        logger.error(f"Request failed {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    report_data = response.json()
    logger.info(report_data.get("value"))
    return CommandResponse(data=report_data.get("value"))
