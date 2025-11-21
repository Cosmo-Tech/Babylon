import logging
from typing import Any

from click import command

from Babylon.commands.powerbi.workspace.services.powerbi_workspace_api_svc import AzurePowerBIWorkspaceService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
)
from Babylon.utils.response import CommandResponse

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
    service_state = state["services"]
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token, state=service_state)
    response = service.get_current()
    return CommandResponse(data=response, verbose=True)
