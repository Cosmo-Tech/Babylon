import logging

from typing import Any
from click import command
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.decorators import (
    retrieve_state,
<<<<<<< HEAD
    injectcontext,
=======
    wrapcontext,
>>>>>>> cc0b634d (add new state to powerbi)
)
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@retrieve_state
def get_current(
    state: Any,
    powerbi_token: str,
) -> CommandResponse:
    """
    Get a specific workspace information
    """
<<<<<<< HEAD
    service_state = state['services']
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token, state=service_state)
=======
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token, state=state)
>>>>>>> cc0b634d (add new state to powerbi)
    response = service.get_current()
    return CommandResponse(data=response, verbose=True)
