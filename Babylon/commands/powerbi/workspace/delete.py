import logging

from typing import Any
from click import command
from click import option
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import (
    retrieve_state,
    wrapcontext,
)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_powerbi_token()
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@option("--workspace-id", "workspace_id", type=QueryType(), help="Workspace Id PowerBI")
@retrieve_state
def delete(state: Any, powerbi_token: str, workspace_id: str, force_validation: bool) -> CommandResponse:
    """
    Delete workspace from Power Bi APP
    """
    service_state = state['services']
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token, state=service_state)
    service.delete(workspace_id=workspace_id, force_validation=force_validation)
    return CommandResponse.success()
