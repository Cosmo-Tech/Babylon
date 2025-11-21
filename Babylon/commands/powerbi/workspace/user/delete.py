import logging
from typing import Any, Optional

from click import argument, command, option

from Babylon.commands.powerbi.workspace.services.powerb__worskapce_users_svc import (
    AzurePowerBIWorkspaceUserService,
)
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=str, help="Workspace Id PowerBI")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("email", type=str)
@retrieve_state
def delete(
    state: Any,
    powerbi_token: str,
    workspace_id: Optional[str],
    email: str,
    force_validation: Optional[bool] = False,
) -> CommandResponse:
    """
    Delete IDENTIFIER from the power bi workspace
    """
    service_state = state["services"]
    service = AzurePowerBIWorkspaceUserService(powerbi_token=powerbi_token, state=service_state)
    service.delete(workspace_id=workspace_id, force_validation=force_validation, email=email)
    return CommandResponse.success()
