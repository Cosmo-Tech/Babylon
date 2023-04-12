from logging import getLogger
from typing import Optional
import pathlib

from click import argument
from click import command
from click import option
from click import Path

from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.environment import Environment
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request
from ....utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("workspace_name", type=QueryType())
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option("--solution", "solution_id", type=QueryType(), default="%deploy%solution_id")
@option("-i",
        "--workspace-file",
        "workspace_file",
        type=Path(path_type=pathlib.Path),
        help="Your custom workspace description file (yaml or json)")
@option(
    "-d",
    "--description",
    "workspace_description",
    help="Workspace description",
)
@option(
    "-s",
    "--select",
    "select",
    is_flag=True,
    help="Select this new workspace in configuration ?",
)
@output_to_file
def create(api_url: str,
           azure_token: str,
           workspace_name: str,
           organization_id: str,
           solution_id: str,
           workspace_file: Optional[pathlib.Path] = None,
           workspace_description: Optional[str] = None,
           select: bool = False) -> CommandResponse:
    """
    Register a workspace by sending a description file to the API.
    See the .payload_templates/API files to edit your own file manually if needed
    """
    env = Environment()
    workspace_file = workspace_file or env.working_dir.payload_path / "api/workspace.json"
    details = env.fill_template(workspace_file,
                                data={
                                    "workspace_name": workspace_name,
                                    "workspace_key": workspace_name.replace(" ", ""),
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
    return CommandResponse.success(workspace, verbose=True)
