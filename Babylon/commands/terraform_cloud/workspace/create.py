import json
import logging
import pathlib
import pprint
from typing import Optional

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
from ....utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@describe_dry_run("Would send a workspace creation payload to terraform")
@argument("workspace_name")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "working_directory", "working_directory")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "vcs_identifier", "vcs_identifier")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "vcs_branch", "vcs_branch")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "vcs_oauth_token_id", "vcs_oauth_token_id")
@timing_decorator
@output_to_file
def create(tfc_client: TFC, workspace_name: str, working_directory: str, vcs_identifier: str, vcs_branch: str,
           vcs_oauth_token_id: str) -> CommandResponse:
    """Use given parameters to create a workspace in the organization"""
    env = Environment()

    payload_template = env.working_dir.payload_path / "tfc/workspace_payload_with_github.json"
    payload = env.fill_template(
        payload_template, {
            "workspace_name": workspace_name,
            "working_directory": working_directory,
            "vcs_branch": vcs_branch,
            "vcs_oauth_token_id": vcs_oauth_token_id
        })
    logger.info("Sending payload to terraform")
    try:
        ws = tfc_client.workspaces.create(payload)
    except TFCHTTPUnprocessableEntity as _error:
        logger.error(f"An issue appeared while processing workspace {workspace_name}:")
        logger.error(pprint.pformat(_error.args))
        return CommandResponse.fail()
    logger.info(pprint.pformat(ws['data']))
    return CommandResponse.success(ws.get("data"))
