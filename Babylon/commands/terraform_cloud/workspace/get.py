import logging
from typing import Optional

from click import command, option
from click import argument
import jmespath
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound

from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.clients import pass_tfc_client
from ....utils.typing import QueryType
from ....utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@argument("workspace_id", type=QueryType(), default="%deploy%terraform_cloud_workspace_id")
@output_to_file
@option("--filter", "filter", help="Filter response with a jmespath query")
@timing_decorator
def get(tfc_client: TFC, workspace_id: str, filter: Optional[str] = None) -> CommandResponse:
    """Get a workspace in the organization"""
    try:
        workspace = tfc_client.workspaces.show(workspace_id=workspace_id)
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} does not exist in your terraform organization")
        return CommandResponse.fail()
    workspace_data = workspace.get("data")
    if filter:
        workspace_data = jmespath.search(filter, workspace_data)
    return CommandResponse.success(workspace_data, verbose=True)
