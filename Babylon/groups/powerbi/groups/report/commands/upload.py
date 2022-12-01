import logging
import requests
import os

from click import pass_context
from click import Context
from click import command
from click import argument
from click import Path

from ......utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_platform_key("powerbi_workspace_id")
@argument("pbxi_filename", type=Path(readable=True, dir_okay=False))
def upload(ctx: Context, powerbi_workspace_id: str, pbxi_filename: str):
    """Publish the given pbxi file to the PowerBI workspace"""
    access_token = ctx.obj.token
    header = {"Content-Type": "multipart/form-data", "Authorization": f"Bearer {access_token}"}
    dataset_name = os.path.splitext(pbxi_filename)[0]
    route = f"https://api.powerbi.com/v1.0/myorg/groups/{powerbi_workspace_id}/imports?datasetDisplayName={dataset_name}"
    session = requests.Session()
    with open(pbxi_filename, "rb") as _f:
        response = session.post(url=route, headers=header, files={"file": _f})
    logger.info(response.json())
