import logging
import pathlib

from click import Path
from click import option
from click import argument
from Babylon.commands.azure.ad.app.service.api import AzureDirectoyAppService
from Babylon.utils.typing import QueryType
from click import Context, command, pass_context
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, wrapcontext

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_context
@output_to_file
@pass_azure_token("graph")
@option("--file",
        "registration_file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        help="path file payload")
@option("--select", "select", is_flag=True, default=True, help="Save this new organization in configuration")
@argument("name", type=QueryType())
def create(ctx: Context, azure_token: str, name: str, select: bool, registration_file: pathlib.Path) -> CommandResponse:
    """
    Register an app in Active Directory
    https://learn.microsoft.com/en-us/graph/api/application-post-applications
    """
    apiApp = AzureDirectoyAppService()
    response = apiApp.create(name=name, azure_token=azure_token, registration_file=registration_file)
    return CommandResponse.success(response, verbose=True)
