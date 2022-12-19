import logging
from typing import Optional

import requests
from click import Context
from click import command
from click import option
from click import pass_context

from ......utils.decorators import require_deployment_key
from ......utils.logging import table_repr
from ......utils.response import CommandResponse

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
    workspace_data = response.json().get("value")
    logger.info(workspace_data)
    if not workspace_data:
        logger.error(f"{workspace_id} was not found")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)

    logger.info("\n".join(table_repr(workspace_data)))
    return CommandResponse(data=workspace_data)
