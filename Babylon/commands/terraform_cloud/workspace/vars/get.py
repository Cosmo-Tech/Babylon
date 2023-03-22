import logging
import pprint

from click import argument
from click import command
from click import option
from terrasnek.api import TFC

from .list_all_vars import list_all_vars
from .....utils.decorators import timing_decorator
from .....utils.typing import QueryType
from .....utils.response import CommandResponse
from .....utils.clients import pass_tfc_client
from .....utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@option("-w",
        "--workspace",
        "workspace_id",
        help="Id of the workspace to use",
        default="%deploy%terraform_cloud_workspace_id",
        type=QueryType())
@argument("var_key", type=QueryType())
@output_to_file
@timing_decorator
def get(tfc_client: TFC, workspace_id: str, var_key: str) -> CommandResponse:
    """Get VAR_KEY variable in a workspace"""
    r = list(v for v in list_all_vars(tfc_client, workspace_id) if v['attributes']['key'] == var_key)

    if not r:
        logger.error(f"Var {var_key} is not set for workspace {workspace_id}")
        return CommandResponse.fail()

    logger.info(pprint.pformat(r[0]))
    return CommandResponse.success(r[0])
