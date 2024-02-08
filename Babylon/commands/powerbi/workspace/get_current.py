import logging

from typing import Any
from click import command
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.decorators import (
    retrieve_state,
    wrapcontext,
)
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@retrieve_state
def get_current(
    state: Any,
    powerbi_token: str,
) -> CommandResponse:
    """
    Get a specific workspace information
    """
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token, state=state)
    response = service.get_current()
    return CommandResponse(data=response, verbose=True)
