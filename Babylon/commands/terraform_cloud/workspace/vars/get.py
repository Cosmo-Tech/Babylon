import logging
import pprint

from click import argument
from click import command
from terrasnek.api import TFC
from .list_all_vars import list_all_vars
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_tfc_client
from Babylon.utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
@output_to_file
@pass_tfc_client
@argument("workspace_id", type=QueryType())
@argument("var_key", type=QueryType())
def get(tfc_client: TFC, workspace_id: str, var_key: str) -> CommandResponse:
    """
    Get VAR_KEY variable in a workspace
    """
    r = list(v for v in list_all_vars(tfc_client, workspace_id) if v['attributes']['key'] == var_key)

    if not r:
        logger.error(f"Var {var_key} is not set for workspace {workspace_id}")
        return CommandResponse.fail()

    logger.info(pprint.pformat(r[0]))
    return CommandResponse.success(r[0])
