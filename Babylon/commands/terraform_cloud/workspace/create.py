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

from ....utils.decorators import describe_dry_run
from ....utils.decorators import timing_decorator
from ....utils.decorators import working_dir_requires_yaml_key
from ....utils.environment import Environment
from ....utils.response import CommandResponse
from ....utils.clients import pass_tfc_client

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
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
@timing_decorator
def create(tfc_client: TFC, workspace_name: str, working_directory: str, vcs_identifier: str, vcs_branch: str,
           vcs_oauth_token_id: str, output_file: Optional[pathlib.Path], select: bool) -> CommandResponse:
    """Use given parameters to create a workspace in the organization"""
    env = Environment()
    workspace_payload = env.fill_template(".payload_templates/tfc/workspace_payload_with_github.json", {
        "workspace_name": workspace_name,
        "working_directory": working_directory,
        "vcs_branch": vcs_branch,
        "vcs_identifier": vcs_identifier,
        "vcs_oauth_token_id": vcs_oauth_token_id
    },
                                          use_working_dir=True)

    logger.info("Sending payload to terraform")
    try:
        ws = tfc_client.workspaces.create(payload=workspace_payload)
    except TFCHTTPUnprocessableEntity as _error:
        logger.error(f"An issue appeared while processing workspace {workspace_name}:")
        logger.error(pprint.pformat(_error.args))
        return CommandResponse.fail()
    logger.info(pprint.pformat(ws['data']))

    if select:
        env.store_data(["terraform", "workspace_id"], ws['data']['id'])
        env.store_data(["terraform", "workspace_name"], workspace_name)

    if output_file:
        with open(output_file, "w") as _file:
            json.dump(ws['data'], _file, ensure_ascii=False)
    return CommandResponse.success(ws.get("data"))
