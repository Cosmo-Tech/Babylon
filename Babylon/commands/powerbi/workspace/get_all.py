import logging

from click import command

from Babylon.commands.powerbi.workspace.services.powerbi_workspace_api_svc import AzurePowerBIWorkspaceService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, output_to_file
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
def get_all(powerbi_token: str) -> CommandResponse:
    """
    Get all workspace information for the given account
    """
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token)
    response = service.get_all()
    return CommandResponse.success(response, verbose=True)
