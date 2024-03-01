import logging

from typing import Any, Optional
from click import command
from click import option
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("--name", "name", help="PowerBI workspace name", type=QueryType())
@retrieve_state
def get(
    state: Any,
    powerbi_token: str,
    workspace_id: Optional[str] = None,
    name: Optional[str] = None,
) -> CommandResponse:
    """
    Get a specific workspace information
    """
    service_state = state['services']
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token, state=service_state)
    response = service.get(workspace_id=workspace_id, name=name)
    return CommandResponse.success(response, verbose=True)
