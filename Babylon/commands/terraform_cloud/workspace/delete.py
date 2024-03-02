import logging

from click import command
from click import option
from click import argument
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound
from Babylon.utils.decorators import describe_dry_run
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_tfc_client


logger = logging.getLogger("Babylon")


@command()
@timing_decorator
@pass_tfc_client
@describe_dry_run("Would send query to delete WORKSPACE_ID to terraform")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("workspace_id", type=str)
def delete(tfc_client: TFC, workspace_id: str, force_validation: bool) -> CommandResponse:
    """
    Delete a workspace from the organization
    """
    if not force_validation and not confirm_deletion("workspace", str(workspace_id)):
        return CommandResponse.fail()
    try:
        tfc_client.workspaces.destroy(workspace_id=workspace_id)
        logger.info(f"Workspace {workspace_id} has been deleted")
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} does not exist in your terraform organization")
        return CommandResponse.fail()
    return CommandResponse.success()
