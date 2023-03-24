import logging

from click import command
from click import argument
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
@timing_decorator
def get(tfc_client: TFC, workspace_id: str) -> CommandResponse:
    """Get a workspace in the organization"""
    try:
        ws = tfc_client.workspaces.show(workspace_id=workspace_id)
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} does not exist in your terraform organization")
        return CommandResponse.fail()
    return CommandResponse.success(ws.get("data"), verbose=True)
