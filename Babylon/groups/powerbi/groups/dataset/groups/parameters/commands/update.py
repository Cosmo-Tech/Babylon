import logging
from typing import Optional
from string import Template
import pathlib

from azure.core.credentials import AccessToken
from click import command
from click import Context
from click import pass_context
from click import argument
from click import Path
from click import option

from ........utils.decorators import require_deployment_key
from ........utils.request import oauth_request
from ........utils.environment import Environment
from ........utils.response import CommandResponse
from ........utils import TEMPLATE_FOLDER_PATH

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id", required=False)
@argument("dataset_id")
@option("-f", "--file", "update_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path), required=True)
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the parameter file path be relative to Babylon working directory ?")
def update(ctx: Context,
           powerbi_workspace_id: str,
           dataset_id: str,
           update_file: str,
           workspace_id: Optional[str] = None,
           use_working_dir_file: bool = False) -> CommandResponse:
    """Update parameters of a given dataset"""
    access_token = ctx.find_object(AccessToken).token
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    # Preparing parameter data
    env = ctx.find_object(Environment)
    if use_working_dir_file:
        update_file = env.working_dir.get_file(str(update_file))
    with open(update_file, "r") as _file:
        template = _file.read()
        data = {**env.configuration.get_deploy(), **env.configuration.get_platform()}
        try:
            details = Template(template).substitute(data)
        except Exception as e:
            logger.error(f"Could not fill parameters template: {e}")
            return CommandResponse.fail()
    update_url = (f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}"
                  f"/datasets/{dataset_id}/Default.UpdateParameters")
    response = oauth_request(url=update_url, access_token=access_token, data=details, type="POST")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully updated dataset {dataset_id} parameters")
    return CommandResponse.success()
