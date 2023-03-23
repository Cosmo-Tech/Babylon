from logging import getLogger

from click import argument
from click import command
from click import option

from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.environment import Environment
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@argument("workspace_id", type=QueryType())
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option("--solution", "solution_id", type=QueryType(), default="%deploy%solution_id")
@option(
    "-i",
    "--workspace-file",
    "workspace_file",
    required=True,
    help="Your custom workspace description file",
)
@output_to_file
def update(api_url: str, azure_token: str, workspace_id: str, organization_id: str,
           workspace_file: str) -> CommandResponse:
    """
    Register a workspace by sending a description file to the API.
    Edit and use the workspace file template located in `API/workspace.json`
    """
    env = Environment()
    workspace_file = workspace_file or env.working_dir.payload_path / "api/workspace.json"
    details = env.fill_template(workspace_file)
    response = oauth_request(f"{api_url}/organizations/{organization_id}/workspaces/{workspace_id}",
                             azure_token,
                             type="PATCH",
                             data=details)
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    logger.info(f"Successfully updated workspace {workspace['id']}")
    return CommandResponse.success(workspace, verbose=True)
