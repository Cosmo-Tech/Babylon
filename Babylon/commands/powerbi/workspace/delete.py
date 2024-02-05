import logging

from typing import Any
from click import command
from click import option
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.environment import Environment
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_powerbi_token()
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@option("--workspace-id", "workspace_id", type=QueryType(), help="Workspace Id PowerBI")
@inject_context_with_resource({"powerbi": ["workspace"]})
def delete(
    context: Any, powerbi_token: str, workspace_id: str, force_validation: bool
) -> CommandResponse:
    """
    Delete workspace from Power Bi APP
    """
    api_powerbi_wrokspace = AzurePowerBIWorkspaceService(
        powerbi_token=powerbi_token, state=context
    )
    api_powerbi_wrokspace.delete(
        workspace_id=workspace_id, force_validation=force_validation
    )
    return CommandResponse.success()
