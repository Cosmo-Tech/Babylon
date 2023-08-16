import logging

from click import command
from terrasnek.api import TFC
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_tfc_client
from Babylon.utils.decorators import output_to_file

logger = logging.getLogger("Babylon")


@command()
@timing_decorator
@output_to_file
@pass_tfc_client
def get_all(tfc_client: TFC) -> CommandResponse:
    """
    Get all available workspaces in the organization
    """
    ws = tfc_client.workspaces.list()

    def get_last_changed(_r):
        return _r.get('attributes', {}).get('latest-change-at', '')

    workspaces = [_ws for _ws in sorted(ws.get('data'), key=get_last_changed)]
    return CommandResponse.success({"workspaces": workspaces}, verbose=True)
