import logging
import pprint
from typing import Optional

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
@option("-w", "--workspace", "workspace_id", help="Id of the workspace to use", required=True, type=QueryType())
@output_to_file
@timing_decorator
def get_all(tfc_client: TFC, workspace_id: Optional[str]) -> CommandResponse:
    """Get all available variables in the workspace"""
    r = list_all_vars(tfc_client, workspace_id)
    if not r:
        logger.warning(f"No vars are set for workspace {workspace_id}")
    for ws_var in r:
        logger.info(pprint.pformat(ws_var))
    return CommandResponse.success({"vars": r})
