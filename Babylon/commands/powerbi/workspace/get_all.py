import logging

from typing import Optional
from click import command
from click import option
from Babylon.commands.powerbi.workspace.services.powerbi_workspace_api_svc import AzurePowerBIWorkspaceService
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file, injectcontext
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
@option("--filter", "filter", help="Filter response with a jmespath query")
def get_all(powerbi_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all workspace information for the given account
    """
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token)
    response = service.get_all(filter=filter)
    return CommandResponse.success(response, verbose=True)
