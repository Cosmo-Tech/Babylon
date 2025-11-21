import logging
from typing import Optional

from click import command, option

from Babylon.commands.powerbi.workspace.services.powerbi_workspace_api_svc import AzurePowerBIWorkspaceService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, output_to_file
from Babylon.utils.response import CommandResponse

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
