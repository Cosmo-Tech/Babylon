import logging
import requests
from typing import Optional

from click import command
from click import option
from click import pass_context
from click import Context

from ......utils.response import CommandResponse
from ......utils.decorators import require_deployment_key

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
@option("-i", "--id", "id")
@option("-n", "--name", "name")
def get(ctx: Context,
        powerbi_workspace_id: str,
        workspace_id: Optional[str] = None,
        id: Optional[str] = None,
        name: Optional[str] = None) -> CommandResponse:
    """Get a specific workspace information"""
    workspace_id = id or workspace_id or powerbi_workspace_id
    url_groups = 'https://api.powerbi.com/v1.0/myorg/groups'
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    params = {"$filter": f"id eq '{workspace_id}'"} if workspace_id else {"$filter": f"name eq '{name}'"}
    try:
        response = requests.get(url=url_groups, headers=header, params=params)
    except Exception as e:
        logger.error(f"Request failed {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    logger.info(response.json())
    return CommandResponse(data=response.json())
