import logging
import requests
from typing import Optional
from string import Template
import pathlib

from click import command
from click import Context
from click import pass_context
from click import argument
from click import Path
from click import option

from ........utils.decorators import require_deployment_key
from ........utils.environment import Environment
from ........utils.response import CommandResponse
from ........utils import TEMPLATE_FOLDER_PATH

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id")
@argument("dataset_id")
@option("-f", "--file", "update_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
def update(ctx: Context,
           powerbi_workspace_id: str,
           dataset_id: str,
           update_file: str,
           workspace_id: Optional[str] = None) -> CommandResponse:
    """Update parameters of a given dataset"""
    access_token = ctx.obj.token
    workspace_id = workspace_id or powerbi_workspace_id
    header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    update_url = (f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
                  f"/datasets/{dataset_id}/Default.UpdateParameters")
    update_file = update_file or f"{TEMPLATE_FOLDER_PATH}/working_dir_template/powerbi_parameters.json"
    with open(update_file, "r") as _file:
        template = _file.read()
        env = ctx.find_object(Environment)
        data = {**env.configuration.get_deploy(), **env.configuration.get_platform()}
        details = Template(template).substitute(data)
    try:
        response = requests.post(url=update_url, data=details, headers=header)
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    if response.status_code != 200:
        logger.error(f"Request failed: {response.text}")
        return CommandResponse(status_code=CommandResponse.STATUS_ERROR)
    logger.info(f"Successfully updated dataset datasource {response.text}")
    return CommandResponse()
