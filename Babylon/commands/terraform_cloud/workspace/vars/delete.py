import logging

from click import argument
from click import command
from click import option
from terrasnek.api import TFC

from .list_all_vars import list_all_vars
from .....utils.decorators import describe_dry_run
from .....utils.decorators import timing_decorator
from .....utils.interactive import confirm_deletion
from .....utils.typing import QueryType
from .....utils.response import CommandResponse
from .....utils.clients import pass_tfc_client

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@describe_dry_run("Would look up id for VAR_KEY in WORKSPACE_ID Then would send delete query to the API for it")
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use", required=True, type=QueryType())
@option("-f", "--force", "force_validation", is_flag=True, help="Should validation be skipped ?")
@argument("var_key", type=QueryType())
@timing_decorator
def delete(tfc_client: TFC, workspace_id: str, var_key: str, force_validation: bool) -> CommandResponse:
    """Delete VAR_KEY variable in a workspace"""

    if not force_validation and not confirm_deletion("variable", var_key):
        return CommandResponse.fail()

    r = list(
        v for v in list_all_vars(tfc_client, workspace_id, lookup_var_sets=False) if v['attributes']['key'] == var_key)

    if not r:
        logger.error(f"Var {var_key} is not set for workspace {workspace_id}")
        return CommandResponse.fail()

    var_id = r[0]['id']
    logger.info(f"Found ID {var_id} for var {var_key} in workspace {workspace_id}")

    logger.info(f"Deleting {var_key} from workspace {workspace_id}")

    r = tfc_client.workspace_vars.destroy(workspace_id=workspace_id, variable_id=var_id)
    return CommandResponse.success()
