import logging
from typing import Optional

import click
from click import command
from click import option
from terrasnek.api import TFC
from terrasnek.exceptions import TFCHTTPNotFound

from ......utils.decorators import describe_dry_run
from ......utils.decorators import timing_decorator
from ......utils.decorators import working_dir_requires_yaml_key
from ......utils.environment import Environment
from ......utils.interactive import confirm_deletion
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")

pass_tfc = click.make_pass_decorator(TFC)


@command()
@pass_tfc
@describe_dry_run("Would send query to delete WORKSPACE_ID to terraform")
@option("-f", "--force", "force_validation", is_flag=True, help="Should validation be skipped ?")
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "workspace_id", "workspace_id_wd")
@timing_decorator
def delete(api: TFC, workspace_id_wd: str, workspace_id: Optional[str], force_validation: bool) -> CommandResponse:
    """Delete a workspace from the organization"""

    env = Environment()

    workspace_id = workspace_id_wd or workspace_id

    if not force_validation and not confirm_deletion("workspace", str(workspace_id)):
        return CommandResponse.fail()

    try:
        api.workspaces.destroy(workspace_id=workspace_id)
        logger.info(f"Workspace {workspace_id} has been deleted")
    except TFCHTTPNotFound:
        logger.error(f"Workspace {workspace_id} does not exist in your terraform organization")
        return CommandResponse.fail()

    if workspace_id_wd == workspace_id:
        logger.info("Unsetting key workspace_id from working dir file as it does not exists anymore")
        env.working_dir.set_yaml_key("terraform_workspace.yaml", "workspace_id", "")
    return CommandResponse()
