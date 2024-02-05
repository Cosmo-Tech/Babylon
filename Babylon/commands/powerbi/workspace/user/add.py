import logging

from typing import Any, Optional
from click import Choice
from click import argument
from click import command
from click import option
from Babylon.commands.powerbi.workspace.user.service.api import (
    AzurePowerBIWorkspaceUserService,
)
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=QueryType(), help="Workspace Id PowerBI")
@argument("identifier", type=QueryType())
@argument("type", type=Choice(["App", "Group", "User", "None"], case_sensitive=False))
@argument(
    "right",
    type=Choice(
        ["Admin", "Contributor", "Member", "Viewer", "None"], case_sensitive=False
    ),
)
@inject_context_with_resource({"powerbi": ["workspace"], "azure": ["email"]})
def add(
    context: Any,
    powerbi_token: str,
    workspace_id: Optional[str],
    identifier: str,
    type: str,
    right: str,
) -> CommandResponse:
    """
    Adds a new user to the power bi workspace using the following information:
    """
    api_powerbi_work_user = AzurePowerBIWorkspaceUserService(
        powerbi_token=powerbi_token, state=context
    )
    api_powerbi_work_user.add(
        workspace_id=workspace_id, right=right, type=type, email=identifier
    )
    return CommandResponse.success()
