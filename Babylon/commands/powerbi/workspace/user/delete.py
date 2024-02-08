import logging

from typing import Any, Optional
from click import argument
from click import command
from click import option
from Babylon.commands.powerbi.workspace.user.service.api import (
    AzurePowerBIWorkspaceUserService,
)
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=QueryType(), help="Workspace Id PowerBI")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("email", type=QueryType())
@inject_context_with_resource({"powerbi": ["workspace"]})
def delete(
    context: Any,
    powerbi_token: str,
    workspace_id: Optional[str],
    email: str,
    force_validation: Optional[bool] = False,
) -> CommandResponse:
    """
    Delete IDENTIFIER from the power bi workspace
    """
    service = AzurePowerBIWorkspaceUserService(
        powerbi_token=powerbi_token, state=context
    )
    service.delete(
        workspace_id=workspace_id, force_validation=force_validation, email=email
    )
    return CommandResponse.success()
