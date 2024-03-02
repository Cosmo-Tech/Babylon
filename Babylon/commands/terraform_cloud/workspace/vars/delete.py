import logging

from click import argument
from click import command
from click import option
from terrasnek.api import TFC
from .list_all_vars import list_all_vars
from Babylon.utils.decorators import describe_dry_run
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.interactive import confirm_deletion

from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_tfc_client

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
@pass_tfc_client
@describe_dry_run("Would look up id for VAR_KEY in WORKSPACE_ID Then would send delete query to the API for it")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("workspace_id", type=str)
@argument("var_key", type=str)
def delete(tfc_client: TFC, workspace_id: str, var_key: str, force_validation: bool) -> CommandResponse:
    """
    Delete VAR_KEY variable in a workspace
    """

    if not force_validation and not confirm_deletion("variable", var_key):
        return CommandResponse.fail()

    r = list(v for v in list_all_vars(tfc_client, workspace_id, lookup_var_sets=False)
             if v['attributes']['key'] == var_key)

    if not r:
        logger.error(f"Var {var_key} is not set for workspace {workspace_id}")
        return CommandResponse.fail()

    var_id = r[0]['id']
    logger.info(f"Found ID {var_id} for var {var_key} in workspace {workspace_id}")

    logger.info(f"Deleting {var_key} from workspace {workspace_id}")

    r = tfc_client.workspace_vars.destroy(workspace_id=workspace_id, variable_id=var_id)
    return CommandResponse.success()
