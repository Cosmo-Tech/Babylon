import logging

from typing import Any, Optional
from click import command
from click import option
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment

from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import (
    retrieve_state,
<<<<<<< HEAD
<<<<<<< HEAD
    injectcontext,
=======
    wrapcontext,
>>>>>>> cc0b634d (add new state to powerbi)
=======
    injectcontext,
>>>>>>> 53b0a6f8 (add injectcontext)
)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_powerbi_token()
<<<<<<< HEAD
<<<<<<< HEAD
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option("--name", "name", help="PowerBI workspace name", type=str)
=======
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("--name", "name", help="PowerBI workspace name", type=QueryType())
>>>>>>> cc0b634d (add new state to powerbi)
=======
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option("--name", "name", help="PowerBI workspace name", type=str)
>>>>>>> cb4637b4 (remove querytype)
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
<<<<<<< HEAD
    service_state = state['services']
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token, state=service_state)
=======
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token, state=state)
>>>>>>> cc0b634d (add new state to powerbi)
    response = service.get(workspace_id=workspace_id, name=name)
    return CommandResponse.success(response, verbose=True)
