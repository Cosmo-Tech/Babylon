import logging

from click import command
from click import argument
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.decorators import output_to_file, wrapcontext
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@output_to_file
@pass_powerbi_token()
@argument("name", type=QueryType())
def create(powerbi_token: str, name: str, select: bool) -> CommandResponse:
    """
    Create workspace named WORKSPACE_NAME into Power Bi App
    """
    api_powerbi_wrokspace = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token)
    response = api_powerbi_wrokspace.create(name=name)
    return CommandResponse.success(response, verbose=True)
