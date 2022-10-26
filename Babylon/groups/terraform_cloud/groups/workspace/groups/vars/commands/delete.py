import logging
from typing import Optional

import click
from click import argument
from click import command
from click import confirm
from click import option
from click import prompt
from terrasnek.api import TFC

from ..list_all_vars import list_all_vars
from ........utils.decorators import allow_dry_run
from ........utils.decorators import working_dir_requires_yaml_key

logger = logging.getLogger("Babylon")

pass_tfc = click.make_pass_decorator(TFC)


@command()
@pass_tfc
@allow_dry_run
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use")
@option("-f", "--force", "force", is_flag=True, help="Should validation be skipped ?")
@working_dir_requires_yaml_key("terraform_workspace.yaml", "workspace_id", "workspace_id_wd")
@argument("var_key")
def delete(api: TFC,
           workspace_id_wd: str,
           workspace_id: Optional[str],
           var_key: str,
           dry_run: bool,
           force: bool):
    """Delete VAR_KEY variable in a workspace"""
    workspace_id = workspace_id or workspace_id_wd

    if not force:
        if not confirm(f"You are trying to delete var {var_key} \nDo you want to continue?"):
            logger.info("Variable deletion aborted.")
            return

        confirm_var_key = prompt("Confirm variable key ")
        if confirm_var_key != var_key:
            logger.error("The variable key you typed did not match, delete canceled.")
            return
        logger.info(f"Deleting variable {var_key}")
    else:
        logger.info(f"Force deleting variable {var_key}")

    if dry_run:
        logger.info(f"DRY RUN - Would look up id for var {var_key} in workspace {workspace_id}")
        logger.info("DRY RUN - Would send delete query to the API for the variable")
    else:
        r = list(v
                 for v in list_all_vars(api, workspace_id, lookup_var_sets=False)
                 if v['attributes']['key'] == var_key)

        if not r:
            logger.error(f"Var {var_key} is not set for workspace {workspace_id}")
            return

        var_id = r[0]['id']
        logger.info(f"Found ID {var_id} for var {var_key} in workspace {workspace_id}")

        logger.info(f"Deleting {var_key} from workspace {workspace_id}")

        r = api.vars.destroy(variable_id=var_id)
