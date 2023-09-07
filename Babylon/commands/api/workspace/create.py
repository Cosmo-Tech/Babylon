import pathlib
from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import option

from ....utils.credentials import pass_azure_token
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.decorators import timing_decorator
from ....utils.environment import Environment
from ....utils.request import oauth_request
from ....utils.response import CommandResponse
from ....utils.typing import QueryType
from ....utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("workspace_file", type=pathlib.Path)
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option("--solution", "solution_id", type=QueryType(), default="%deploy%solution_id")
@option("--workspace-name", "workspace_name", type=QueryType(), help="Your custom workspace name")
@option(
    "-d",
    "--description",
    "workspace_description",
    help="Workspace description",
)
@option("-s", "--select", "select", is_flag=True, default=True, help="Select the created workspace")
@output_to_file
def create(
    api_url: str,
    azure_token: str,
    organization_id: str,
    solution_id: str,
    workspace_file: pathlib.Path,
    select: bool,
    workspace_name: Optional[str] = None,
    workspace_description: Optional[str] = None,
) -> CommandResponse:
    """
    Register a workspace by sending a description file to the API.
    See the .payload_templates/API files to edit your own file manually if needed
    """
    env = Environment()
    workspace_details = env.working_dir.get_file_content(workspace_file)
    workspace_key = workspace_name.replace(" ", "") if workspace_name else workspace_details["name"].replace(" ", "")
    details = env.fill_template(workspace_file,
                                data={
                                    "workspace_name": workspace_name,
                                    "workspace_key": workspace_key,
                                    "workspace_description": workspace_description,
                                    "solution_id": solution_id
                                })
    if workspace_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/organizations/{organization_id}/workspaces",
                             azure_token,
                             type="POST",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    logger.info(f"Successfully created workspace {workspace['id']}")
    if select:
        logger.info("Updated configuration variables with workspace_id")
        env.configuration.set_deploy_var("workspace_id", workspace["id"])
        env.configuration.set_deploy_var("workspace_key", workspace["key"])
    return CommandResponse.success(workspace, verbose=True)
