import logging

from typing import Any, Optional
from click import Choice
from click import argument
from click import command
from click import option
from Babylon.commands.powerbi.workspace.services.powerb__worskapce_users_svc import (
    AzurePowerBIWorkspaceUserService, )
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=str, help="Workspace Id PowerBI")
@argument("email", type=str)
@argument("type", type=Choice(["App", "Group", "User", "None"], case_sensitive=False))
@argument(
    "right",
    type=Choice(["Admin", "Contributor", "Member", "Viewer", "None"], case_sensitive=False),
)
@retrieve_state
def update(
    state: Any,
    powerbi_token: str,
    workspace_id: Optional[str],
    email: str,
    type: str,
    right: str,
) -> CommandResponse:
    """
    Updates an existing user in the power bi workspace
    """
    service_state = state['services']
    service = AzurePowerBIWorkspaceUserService(powerbi_token=powerbi_token, state=service_state)
    response = service.update(workspace_id=workspace_id, right=right, type=type, email=email)
    response = response.json()
    return CommandResponse.success(response)
