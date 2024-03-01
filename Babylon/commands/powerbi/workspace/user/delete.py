import logging

from typing import Any, Optional
from click import argument
from click import command
from click import option
from Babylon.commands.powerbi.workspace.user.service.api import (
<<<<<<< HEAD
    AzurePowerBIWorkspaceUserService, )
from Babylon.utils.decorators import retrieve_state, injectcontext
<<<<<<< HEAD

=======
    AzurePowerBIWorkspaceUserService,
)
from Babylon.utils.decorators import retrieve_state, wrapcontext
=======
>>>>>>> 53b0a6f8 (add injectcontext)
from Babylon.utils.typing import QueryType
>>>>>>> cc0b634d (add new state to powerbi)
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=str, help="Workspace Id PowerBI")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
<<<<<<< HEAD
@argument("email", type=str)
=======
@argument("email", type=QueryType())
>>>>>>> cc0b634d (add new state to powerbi)
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
<<<<<<< HEAD
    service_state = state["services"]
    service = AzurePowerBIWorkspaceUserService(powerbi_token=powerbi_token, state=service_state)
    service.delete(workspace_id=workspace_id, force_validation=force_validation, email=email)
=======
    service = AzurePowerBIWorkspaceUserService(powerbi_token=powerbi_token, state=state)
    service.delete(
        workspace_id=workspace_id, force_validation=force_validation, email=email
    )
>>>>>>> cc0b634d (add new state to powerbi)
    return CommandResponse.success()
