import logging

from click import option
from click import command
from typing import Optional
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, injectcontext
from Babylon.commands.azure.ad.services.ad_group_svc import AzureDirectoyGroupService

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_azure_token("graph")
@option("--filter", "filter", help="Filter response with a jmespath query")
def get_all(azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all AD groups from current subscription
    https://learn.microsoft.com/en-us/graph/api/group-list
    """
    service = AzureDirectoyGroupService(azure_token=azure_token)
    response = service.get_all(filter=filter)
    return CommandResponse.success(response, verbose=True)
