import logging
import requests
from typing import Optional
import json

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
@option(
    "-o",
    "--output_file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
    type=str,
)
def get(ctx: Context,
        powerbi_workspace_id: str,
        dataset_id: str,
        workspace_id: Optional[str] = None,
        output_file: Optional[str] = None) -> CommandResponse:
    """Get datasource details of a given dataset"""
    workspace_id = workspace_id or powerbi_workspace_id
    access_token = ctx.obj.token
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    update_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/datasources"
    try:
        response = requests.get(url=update_url, headers=header)
    except Exception as e:
        logger.error(f"Request failed {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    if response.status_code != 200:
        logger.error(f"Request failed {response.text}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    output_data = response.json().get("value")
    if not output_file:
        logger.info("\n".join([str(data) for data in output_data]))
        return CommandResponse(data=output_data)
    with open(output_file, "w") as _file:
        json.dump(output_data, _file, ensure_ascii=False)
        logger.info("Full content was dumped on %s.", output_file)
    return CommandResponse(data=output_data)
