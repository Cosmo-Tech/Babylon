import logging

from typing import Any, Optional
from click import command
from click import option
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("--name", "name", help="PowerBI workspace name", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def get(
    context: Any,
    powerbi_token: str,
    workspace_id: Optional[str] = None,
    name: Optional[str] = None,
) -> CommandResponse:
    """
    Get a specific workspace information
    """
    api_powerbi_wrokspace = AzurePowerBIWorkspaceService(
        powerbi_token=powerbi_token, state=context
    )
    response = api_powerbi_wrokspace.get(workspace_id=workspace_id, name=name)
    return CommandResponse.success(response, verbose=True)
