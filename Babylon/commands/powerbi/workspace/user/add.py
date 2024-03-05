import logging

from typing import Any, Optional
from click import Choice
from click import argument
from click import command
from click import option

from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)
from Babylon.commands.powerbi.workspace.user.service.api import (
    AzurePowerBIWorkspaceUserService,
)
logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=str, help="Workspace Id PowerBI")
@argument("identifier", type=str)
@argument("type", type=Choice(["App", "Group", "User", "None"], case_sensitive=False))
@argument(
    "right",
    type=Choice(["Admin", "Contributor", "Member", "Viewer", "None"], case_sensitive=False),
)
@retrieve_state
def add(
    state: Any,
    powerbi_token: str,
    workspace_id: Optional[str],
    identifier: str,
    type: str,
    right: str,
) -> CommandResponse:
    """
    Adds a new user to the power bi workspace using the following information:
    """
    service_state = state['services']
    service = AzurePowerBIWorkspaceUserService(powerbi_token=powerbi_token, state=service_state)
    service.add(workspace_id=workspace_id, right=right, type=type, email=identifier)
    return CommandResponse.success()
