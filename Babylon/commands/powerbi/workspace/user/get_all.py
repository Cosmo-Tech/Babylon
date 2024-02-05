import logging

from typing import Any, Optional
from click import command
from click import option
from Babylon.commands.powerbi.workspace.user.service.api import (
    AzurePowerBIWorkspaceUserService,
)
from Babylon.utils.decorators import output_to_file, wrapcontext
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@output_to_file
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=QueryType(), help="Workspace Id PowerBI")
@option("--filter", "filter", help="Filter response with a jmespath query")
@inject_context_with_resource({"powerbi": ["workspace"]})
def get_all(
    context: Any, powerbi_token: str, workspace_id: str, filter: Optional[str] = None
) -> CommandResponse:
    """
    List all exisiting users in the power bi workspace
    """
    api_powerbi_work_user = AzurePowerBIWorkspaceUserService(
        powerbi_token=powerbi_token, state=context
    )
    response = api_powerbi_work_user.get_all(workspace_id=workspace_id)
    return CommandResponse.success(response, verbose=True)
