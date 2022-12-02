import logging
import requests
from typing import Optional

from click import command
from click import argument
from click import pass_context
from click import Context
from click import Path
from click import option

from ........utils.decorators import require_deployment_key
from ........utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
@argument("dataset_id")
@argument("update_file", type=Path(readable=True, dir_okay=False))
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
def update(ctx: Context,
           powerbi_workspace_id: str,
           dataset_id: str,
           update_file: str,
           workspace_id: Optional[str] = None) -> CommandResponse:
    """Update datasource"""
    access_token = ctx.obj.token
    workspace_id = workspace_id or powerbi_workspace_id
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    update_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/Default.UpdateParameters"
    with open(update_file, "r") as _file:
        details = _file.read()
    try:
        requests.post(url=update_url, data=details, headers=header)
    except Exception as e:
        logger.error(f"Request failed {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    return CommandResponse()
