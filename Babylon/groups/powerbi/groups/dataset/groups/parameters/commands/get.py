import logging
import requests
from typing import Optional
import json

from click import command
from click import argument
from click import pass_context
from click import Context
from click import option
from click import Path

from ........utils.decorators import require_deployment_key
from ........utils.response import CommandResponse
from ........utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
@argument("dataset_id", type=QueryType())
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
@option(
    "-o",
    "--output-file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
    type=Path(),
)
def get(ctx: Context,
        powerbi_workspace_id: str,
        dataset_id: str,
        workspace_id: Optional[str] = None,
        output_file: Optional[str] = None) -> CommandResponse:
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
    if response.status_code != 200:
        logger.error(f"Request failed: {response.text}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    output_data = response.json().get("value")
    if not output_file:
        logger.info(output_data)
        return CommandResponse(data=output_data)
    with open(output_file, "w") as _file:
        json.dump(output_data, _file, ensure_ascii=False)
    logger.info("Full content was dumped on %s.", output_file)
    return CommandResponse(data=output_data)
