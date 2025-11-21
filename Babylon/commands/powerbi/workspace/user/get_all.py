import logging
from typing import Any, Optional

from click import command, option

from Babylon.commands.powerbi.workspace.services.powerb__worskapce_users_svc import (
    AzurePowerBIWorkspaceUserService,
)
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=str, help="Workspace Id PowerBI")
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, powerbi_token: str, workspace_id: str, filter: Optional[str] = None) -> CommandResponse:
    """
    List all exisiting users in the power bi workspace
    """
    service_state = state["services"]
    service = AzurePowerBIWorkspaceUserService(powerbi_token=powerbi_token, state=service_state)
    response = service.get_all(workspace_id=workspace_id, filter=filter)
    return CommandResponse.success(response, verbose=True)
