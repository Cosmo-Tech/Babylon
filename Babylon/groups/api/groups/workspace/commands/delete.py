from logging import getLogger
from typing import Optional
from click import argument
from click import option
from click import command
from click import confirm
from click import make_pass_decorator
from click import prompt
from cosmotech_api.api.workspace_api import WorkspaceApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.decorators import allow_dry_run
from ......utils.decorators import timing_decorator
from ......utils.decorators import require_deployment_key

logger = getLogger("Babylon")

pass_workspace_api = make_pass_decorator(WorkspaceApi)


@command()
@allow_dry_run
@pass_workspace_api
@timing_decorator
@require_deployment_key("organization_id", "organization_id")
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
@argument("workspace_id")
def delete(
    workspace_api: WorkspaceApi,
    organization_id: str,
    workspace_id: str,
    dry_run: Optional[bool] = False,
    force_validation: Optional[bool] = False,
):
    """Unregister a workspace via Cosmotech APi."""

    if dry_run:
        logger.info("DRY RUN - Would call workspace_api.delete_workspace")
        return

    try:
        workspace_api.find_workspace_by_id(workspace_id=workspace_id, organization_id=organization_id)
    except NotFoundException:
        logger.error(f"Workspace {workspace_id} does not exists in organization {organization_id}.")
        return
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return

    if not force_validation:

        if not confirm(
            f"You are trying to delete workspace {workspace_id} workspaces of organization {organization_id} \nDo you want to continue?"
        ):
            logger.info("Workspace deletion aborted.")
            return

        confirm_workspace_id = prompt("Confirm workspace id ")
        if confirm_workspace_id != workspace_id:
            logger.error("The workspace id you have type didn't mach with workspace you are trying to delete id")
            return

    logger.info(f"Deleting workspace {workspace_id}")

    try:
        workspace_api.delete_workspace(organization_id=organization_id, workspace_id=workspace_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} does not exists.")
        return
    logger.info(f"Workspaces {workspace_id} of organization {organization_id} deleted.")
