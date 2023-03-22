import json
import logging
import pathlib
import pprint

from click import argument
from click import command
from click import Path
from click import option
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPUnprocessableEntity

from ....utils.decorators import describe_dry_run
from ....utils.decorators import timing_decorator
from ....utils.environment import Environment
from ....utils.response import CommandResponse
from ....utils.clients import pass_tfc_client
from ....utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@describe_dry_run("Would send a workspace creation payload to terraform")
@argument("workspace_data_file", type=Path(path_type=pathlib.Path, exists=True, dir_okay=False))
@option("--select", "select", is_flag=True, help="Select the created workspace")
@timing_decorator
@output_to_file
def create(tfc_client: TFC, workspace_data_file: pathlib.Path, select: bool = False) -> CommandResponse:
    """
    Use given parameters to create a workspace in the organization
    Takes a workspace_data_file as input, which should contain the following keys:
    - workspace_name
    - working_directory
    - vcs_branch
    - vcs_identifier
    - vcs_oauth_token_id
    """
    env = Environment()
    workspace_data = env.working_dir.get_file_content(workspace_data_file)
    workspace_keys = {"workspace_name", "working_directory", "vcs_branch", "vcs_identifier", "vcs_oauth_token_id"}
    if set(workspace_data.keys()) != workspace_keys:
        logger.error(f"Workspace data file should contain only keys: {','.join(workspace_keys)}")
        return CommandResponse.fail()

    payload_template = env.working_dir.payload_path / "tfc/workspace_create.json"
    payload = env.fill_template(payload_template, workspace_data)
    payload_data = json.loads(payload)
    try:
        ws = tfc_client.workspaces.create(payload_data)
    except TFCHTTPUnprocessableEntity as _error:
        logger.error(f"An issue appeared while processing workspace {workspace_data['workspace_name']}:")
        logger.error(pprint.pformat(_error.args))
        return CommandResponse.fail()
    logger.info(pprint.pformat(ws['data']))
    if select:
        env.configuration.set_deploy_var("terraform_cloud_workspace_id", ws['data']['id'])
        logger.info(
            f"terraform_cloud_workspace_id: {ws['data']['id']} was successfully set in the deploy configuration")
    return CommandResponse.success(ws.get("data"))
