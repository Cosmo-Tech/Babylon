import logging

from typing import Any, Optional
from click import command
from click import option
from Babylon.commands.powerbi.workspace.user.service.api import (
<<<<<<< HEAD
    AzurePowerBIWorkspaceUserService, )
from Babylon.utils.decorators import output_to_file, retrieve_state, injectcontext

=======
    AzurePowerBIWorkspaceUserService,
)
from Babylon.utils.decorators import output_to_file, retrieve_state, wrapcontext
from Babylon.utils.typing import QueryType
>>>>>>> cc0b634d (add new state to powerbi)
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=str, help="Workspace Id PowerBI")
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
<<<<<<< HEAD
def get_all(state: Any, powerbi_token: str, workspace_id: str, filter: Optional[str] = None) -> CommandResponse:
    """
    List all exisiting users in the power bi workspace
    """
    service_state = state['services']
    service = AzurePowerBIWorkspaceUserService(powerbi_token=powerbi_token, state=service_state)
=======
def get_all(
    state: Any, powerbi_token: str, workspace_id: str, filter: Optional[str] = None
) -> CommandResponse:
    """
    List all exisiting users in the power bi workspace
    """
    service = AzurePowerBIWorkspaceUserService(powerbi_token=powerbi_token, state=state)
>>>>>>> cc0b634d (add new state to powerbi)
    response = service.get_all(workspace_id=workspace_id, filter=filter)
    return CommandResponse.success(response, verbose=True)
