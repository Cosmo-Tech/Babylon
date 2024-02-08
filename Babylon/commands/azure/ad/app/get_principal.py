import logging

from click import command
from click import argument
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, wrapcontext
from Babylon.commands.azure.ad.app.service.api import AzureDirectoyAppService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@output_to_file
@pass_azure_token("graph")
@argument("object_id", type=QueryType())
def get_principal(azure_token: str, object_id: str) -> CommandResponse:
    """
    Get an app registration service principal
    https://learn.microsoft.com/en-us/graph/api/serviceprincipal-get
    """
    service = AzureDirectoyAppService(azure_token=azure_token)
    service.get_principal(object_id=object_id)
    return CommandResponse.success(None, verbose=True)
