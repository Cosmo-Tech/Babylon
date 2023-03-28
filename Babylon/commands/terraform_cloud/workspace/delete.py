import logging

from click import command
from click import option
from click import argument
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound

from ....utils.decorators import describe_dry_run
from ....utils.decorators import timing_decorator
from ....utils.interactive import confirm_deletion
from ....utils.response import CommandResponse
from ....utils.clients import pass_tfc_client
from ....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@describe_dry_run("Would send query to delete WORKSPACE_ID to terraform")
@argument("workspace_id", type=QueryType(), default="%deploy%terraform_cloud_workspace_id")
@option("-f", "--force", "force_validation", is_flag=True, help="Should validation be skipped ?")
@timing_decorator
def delete(tfc_client: TFC, workspace_id: str, force_validation: bool) -> CommandResponse:
    """Delete a workspace from the organization"""
    if not force_validation and not confirm_deletion("workspace", str(workspace_id)):
        return CommandResponse.fail()
    try:
        tfc_client.workspaces.destroy(workspace_id=workspace_id)
        logger.info(f"Workspace {workspace_id} has been deleted")
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} does not exist in your terraform organization")
        return CommandResponse.fail()
    return CommandResponse.success()