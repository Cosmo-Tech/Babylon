from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import confirm
from click import make_pass_decorator
from click import option
from click import prompt
from cosmotech_api.api.workspace_api import WorkspaceApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import allow_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

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
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
    type=bool,
)
@option(
    "-w",
    "--workspace-file",
    "workspace_file",
    help="In case the workspace id is retrieved from a file",
)
@argument("workspace_id", required=False)
def delete(
    workspace_api: WorkspaceApi,
    organization_id: str,
    workspace_file: Optional[str] = None,
    workspace_id: Optional[str] = None,
    dry_run: Optional[bool] = False,
    use_working_dir_file: Optional[bool] = False,
    force_validation: Optional[bool] = False,
):
    """Unregister a workspace via Cosmotech APi."""

    if dry_run:
        logger.info("DRY RUN - Would call workspace_api.delete_workspace")
        return

    if not workspace_id:
        if not workspace_file:
            logger.error("No id passed as argument or option use -d option"
                         " to pass an json or yaml file containing an workspace id.")
            return

        converted_workspace_content = get_api_file(
            api_file_path=workspace_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
        if not converted_workspace_content:
            logger.error("Can not get Workspace definition, please check your file")
            return

        workspace_id = converted_workspace_content["id"] or converted_workspace_content["workspace_id"]
        if not workspace_id:
            logger.error(f"Could not found workspace id in {workspace_file}.")
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
                f"You are trying to delete workspace {workspace_id} workspaces of organization {organization_id} \n"
                "Do you want to continue?"):
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
