from logging import getLogger
from typing import Optional

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.workspace_api import WorkspaceApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import get_api_file
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.environment import Environment
from ......utils.interactive import confirm_deletion
from ......utils.typing import QueryType
from ......utils.response import CommandResponse

logger = getLogger("Babylon")

pass_workspace_api = make_pass_decorator(WorkspaceApi)


@command()
@describe_dry_run("Would call **workspace_api.delete_workspace** to delete a workspace")
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
)
@option(
    "-i",
    "--workspace-file",
    "workspace_file",
    help="In case the workspace id is retrieved from a file",
)
@argument("workspace_id", required=False, type=QueryType())
def delete(
    workspace_api: WorkspaceApi,
    organization_id: str,
    workspace_id: Optional[str] = None,
    workspace_file: Optional[str] = None,
    force_validation: Optional[bool] = False,
    use_working_dir_file: Optional[bool] = False,
) -> CommandResponse:
    """Unregister a workspace via Cosmotech APi."""

    env = Environment()

    if not workspace_id:
        if not workspace_file:
            logger.error("No id passed as argument or option use -i option"
                         " to pass an json or yaml file containing an workspace id.")
            return CommandResponse.fail()

        converted_workspace_content = get_api_file(api_file_path=workspace_file,
                                                   use_working_dir_file=use_working_dir_file)
        if not converted_workspace_content:
            logger.error("Can not get Workspace definition, please check your file")
            return CommandResponse.fail()

        workspace_id = converted_workspace_content.get("id") or converted_workspace_content.get("workspace_id")
        if not workspace_id:
            logger.error("Can not get solution id, please check your file")
            return CommandResponse.fail()

    try:
        workspace_api.find_workspace_by_id(workspace_id=workspace_id, organization_id=organization_id)

    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id : {organization_id} not found.")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Workspace {workspace_id} not found in organization {organization_id}")
        return CommandResponse.fail()

    if not force_validation and not confirm_deletion("workspace", workspace_id):
        return CommandResponse.fail()

    logger.info(f"Deleting workspace {workspace_id}")

    try:
        workspace_api.delete_workspace(organization_id=organization_id, workspace_id=workspace_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Workspace {workspace_id} not found in organization {organization_id}")
        return CommandResponse.fail()
    except ForbiddenException:
        logger.error(f"You are not allowed to delete the workspace : {workspace_id}")
        return CommandResponse.fail()

    env.configuration.set_deploy_var("workspace_id", '')
    env.configuration.set_deploy_var("workspace_key", '')
    logger.info(f"Workspaces {workspace_id} of organization {organization_id} deleted.")

    return CommandResponse.success({"id": workspace_id})
