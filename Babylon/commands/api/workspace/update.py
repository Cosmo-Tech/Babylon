import pathlib
from logging import getLogger

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
@option("--workspace", "workspace_id", type=QueryType(), default="%deploy%workspace_id")
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option("--solution", "solution_id", type=QueryType(), default="%deploy%solution_id")
@argument("workspace_file", type=pathlib.Path)
@output_to_file
def update(
    api_url: str,
    azure_token: str,
    workspace_id: str,
    organization_id: str,
    solution_id: str,
    workspace_file: str,
) -> CommandResponse:
    """
    Register a workspace by sending a description file to the API.
    See the .payload_templates/API files to edit your own file manually if needed
    """
    env = Environment()
    # workspace_file = workspace_file or env.working_dir.payload_path / "api/workspace.json"
    details = env.fill_template(workspace_file)
    if workspace_file.suffix in [".yaml", ".yml"]:
        details = yaml_to_json(details)
    response = oauth_request(f"{api_url}/organizations/{organization_id}/workspaces/{workspace_id}",
                             azure_token,
                             type="PATCH",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    logger.info(f"Successfully updated workspace {workspace['id']}")
    return CommandResponse.success(workspace, verbose=True)
