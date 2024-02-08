import logging

from click import command
from click import argument
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.decorators import output_to_file, injectcontext

from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
<<<<<<< HEAD
@argument("name", type=str)
=======
@argument("name", type=QueryType())
>>>>>>> cc0b634d (add new state to powerbi)
def create(powerbi_token: str, name: str) -> CommandResponse:
    """
    Create workspace named WORKSPACE_NAME into Power Bi App
    """
    service = AzurePowerBIWorkspaceService(powerbi_token=powerbi_token)
    response = service.create(name=name)
    return CommandResponse.success(response, verbose=True)
