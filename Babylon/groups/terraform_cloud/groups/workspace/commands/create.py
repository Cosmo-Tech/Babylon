import json
import logging
import pathlib
import pprint
from typing import Optional

import click
from click import argument
from click import command
from click import option
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPUnprocessableEntity

from ......utils import TEMPLATE_FOLDER_PATH
from ......utils.decorators import describe_dry_run
from ......utils.decorators import working_dir_requires_yaml_key
from ......utils.environment import Environment

logger = logging.getLogger("Babylon")

pass_tfc = click.make_pass_decorator(TFC)


@command()
@pass_tfc
@describe_dry_run("Would send a workspace creation payload to terraform")
@option(
    "-o",
    "--output",
    "output_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, path_type=pathlib.Path),
    help="File to which content should be outputted (json-formatted)",
)
@option("-s",
        "--select",
        "select",
        is_flag=True,
        help="Should the id of the created workspace set in the working dir file ?")
@argument("workspace_name")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "working_directory", "working_directory")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "vcs_identifier", "vcs_identifier")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "vcs_branch", "vcs_branch")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "vcs_oauth_token_id", "vcs_oauth_token_id")
def create(api: TFC, workspace_name: str, working_directory: str, vcs_identifier: str, vcs_branch: str,
           vcs_oauth_token_id: str, output_file: Optional[pathlib.Path], select: bool):
    """Use given parameters to create a workspace in the organization"""
    env = Environment()
    workspace_payload_template = TEMPLATE_FOLDER_PATH / "terraform_cloud/workspace_payload_with_github.json"
    with open(workspace_payload_template) as _f:
        workspace_payload = json.load(_f)
    workspace_payload['data']['attributes']['name'] = workspace_name
    workspace_payload['data']['attributes']['working-directory'] = working_directory
    workspace_payload['data']['attributes']['vcs-repo']['branch'] = vcs_branch
    workspace_payload['data']['attributes']['vcs-repo']['identifier'] = vcs_identifier
    workspace_payload['data']['attributes']['vcs-repo']['oauth-token-id'] = vcs_oauth_token_id

    logger.info("Sending payload to terraform")
    try:
        ws = api.workspaces.create(payload=workspace_payload)
    except TFCHTTPUnprocessableEntity as _error:
        logger.error(f"An issue appeared while processing workspace {workspace_name}:")
        logger.error(pprint.pformat(_error.args))
        return
    logger.info(pprint.pformat(ws['data']))

    if select:
        ws_id = ws['data']['id']
        env.working_dir.set_yaml_key("terraform_workspace.yaml", "workspace_id", ws_id)

    if output_file:
        with open(output_file, "w") as _file:
            json.dump(ws['data'], _file, ensure_ascii=False)
