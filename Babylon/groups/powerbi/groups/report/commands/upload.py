import logging
import requests
import os
from typing import Optional

from click import pass_context
from click import Context
from click import command
from click import argument
from click import Path
from click import option

from ......utils.decorators import require_deployment_key
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
@argument("pbxi_filename", type=Path(readable=True, dir_okay=False))
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
def upload(ctx: Context,
           powerbi_workspace_id: str,
           pbxi_filename: str,
           workspace_id: Optional[str] = None) -> CommandResponse:
    """Publish the given pbxi file to the PowerBI workspace"""
    access_token = ctx.obj.token
    workspace_id = workspace_id or powerbi_workspace_id
    header = {"Content-Type": "multipart/form-data", "Authorization": f"Bearer {access_token}"}
    dataset_name = os.path.splitext(pbxi_filename)[0]
    route = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/imports?datasetDisplayName={dataset_name}"
    session = requests.Session()
    with open(pbxi_filename, "rb") as _f:
        try:
            response = session.post(url=route, headers=header, files={"file": _f})
        except Exception as e:
            logger.error(f"Request failed {e}")
            return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    logger.info(response.json())
    return CommandResponse(response.json())
