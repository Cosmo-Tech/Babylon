import logging
import pprint

from click import command
from terrasnek.api import TFC

from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.clients import pass_tfc_client
from ....utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@output_to_file
@timing_decorator
def get_all(tfc_client: TFC) -> CommandResponse:
    """Get all available workspaces in the organization"""
    ws = tfc_client.workspaces.list()

    def get_last_changed(_r):
        return _r.get('attributes', {}).get('latest-change-at', '')

    workspaces = [_ws for _ws in sorted(ws.get('data'), key=get_last_changed)]
    logger.info(pprint.pformat(workspaces))
    return CommandResponse.success({"workspaces": workspaces})
