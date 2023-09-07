import logging
from typing import Optional

import jmespath
from click import command
from click import option
from terrasnek.api import TFC

from ....utils.clients import pass_tfc_client
from ....utils.decorators import output_to_file
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@pass_tfc_client
@output_to_file
@option("--filter", "filter", help="Filter response with a jmespath query")
@timing_decorator
def get_all(tfc_client: TFC, filter: Optional[str] = None) -> CommandResponse:
    """Get all available workspaces in the organization"""
    ws = tfc_client.workspaces.list_all()

    def get_last_changed(_r):
        return _r.get('attributes', {}).get('latest-change-at', '')

    workspaces = [_ws for _ws in sorted(ws.get('data'), key=get_last_changed)]
    if filter:
        workspaces = jmespath.search(filter, workspaces)
    return CommandResponse.success({"workspaces": workspaces}, verbose=True)
