import logging

from click import argument, command

from Babylon.commands.powerbi.workspace.services.powerbi_workspace_api_svc import AzurePowerBIWorkspaceService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
@argument("name", type=str)
def create(powerbi_token: str, name: str) -> CommandResponse:
    """
    Create workspace named WORKSPACE_NAME into Power Bi App
    """
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token)
    response = service.create(name=name)
    return CommandResponse.success(response, verbose=True)
