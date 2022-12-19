import logging
from typing import Optional

import click
from click import argument
from click import command
from click import option
from terrasnek.api import TFC

from ..list_all_vars import list_all_vars
from ........utils.decorators import describe_dry_run
from ........utils.decorators import timing_decorator
from ........utils.decorators import working_dir_requires_yaml_key
from ........utils.interactive import confirm_deletion

logger = logging.getLogger("Babylon")

pass_tfc = click.make_pass_decorator(TFC)


@command()
@pass_tfc
@describe_dry_run("""Would look up id for VAR_KEY in WORKSPACE_ID

Then would send delete query to the API for it""")
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use")
@option("-f", "--force", "force_validation", is_flag=True, help="Should validation be skipped ?")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "workspace_id", "workspace_id_wd")
@argument("var_key")
@timing_decorator
def delete(api: TFC, workspace_id_wd: str, workspace_id: Optional[str], var_key: str, force_validation: bool):
    """Delete VAR_KEY variable in a workspace"""
    workspace_id = workspace_id or workspace_id_wd

    if not force_validation and not confirm_deletion("variable", var_key):
        return

    r = list(v for v in list_all_vars(api, workspace_id, lookup_var_sets=False) if v['attributes']['key'] == var_key)

    if not r:
        logger.error(f"Var {var_key} is not set for workspace {workspace_id}")
        return

    var_id = r[0]['id']
    logger.info(f"Found ID {var_id} for var {var_key} in workspace {workspace_id}")

    logger.info(f"Deleting {var_key} from workspace {workspace_id}")

    r = api.workspace_vars.destroy(workspace_id=workspace_id, variable_id=var_id)
