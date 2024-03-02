import logging
import pprint

from typing import Optional
from click import argument, command
from terrasnek.api import TFC
from .list_all_vars import list_all_vars
from Babylon.utils.decorators import timing_decorator

from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_tfc_client
from Babylon.utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
@output_to_file
@pass_tfc_client
@argument("workspace_id", type=str)
def get_all(tfc_client: TFC, workspace_id: Optional[str]) -> CommandResponse:
    """
    Get all available variables in the workspace
    """
    r = list_all_vars(tfc_client, workspace_id)
    if not r:
        logger.warning(f"No vars are set for workspace {workspace_id}")
    for ws_var in r:
        logger.info(pprint.pformat(ws_var))
    return CommandResponse.success({"vars": r})
