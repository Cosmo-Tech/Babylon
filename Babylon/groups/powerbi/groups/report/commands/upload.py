import logging
import os
from typing import Optional
import pathlib
import time

import requests
from azure.core.credentials import AccessToken
from click import pass_context
from click import Context
from click import command
from click import argument
from click import Path
from click import option
from rich.pretty import pretty_repr

from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse
from ......utils.request import oauth_request

logger = logging.getLogger("Babylon")

RETRY_WAIT_TIME = 0.5


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id", required=False)
@argument("pbix_filename", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
@timing_decorator
def upload(ctx: Context,
           powerbi_workspace_id: str,
           pbix_filename: str,
           workspace_id: Optional[str] = None) -> CommandResponse:
    """Publish the given pbxi file to the PowerBI workspace"""
    access_token = ctx.find_object(AccessToken).token
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    name = os.path.splitext(pbix_filename)[0]
    header = {"Content-Type": "multipart/form-data", "Authorization": f"Bearer {access_token}"}
    route = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/imports?datasetDisplayName={name}"
    session = requests.Session()
    with open(pbix_filename, "rb") as _f:
        try:
            response = session.post(url=route, headers=header, files={"file": _f})
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return CommandResponse.fail()
        if response.status_code >= 300:
            logger.error(f"Request failed ({response.status_code}): {response.text}")
            return CommandResponse.fail()
    import_data = response.json()
    # Wait for import end
    route = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/imports/{import_data.get('id')}"
    output_data = {}
    while True:
        time.sleep(RETRY_WAIT_TIME)
        response = oauth_request(route, access_token)
        output_data = response.json()
        if output_data.get("importState") != "Publishing":
            break
        logger.info("Waiting for import to finish...")
    if output_data.get("importState") != "Succeeded":
        logger.error(f"Failed to import report file {pbix_filename}")
        return CommandResponse.fail()
    logger.info(pretty_repr(output_data))
    logger.info(f"Successfully imported report {pbix_filename}")
    return CommandResponse.success(output_data)
