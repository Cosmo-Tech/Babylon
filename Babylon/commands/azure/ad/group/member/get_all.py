import logging

from click import command
from click import argument
from Babylon.commands.azure.ad.services.member import AzureDirectoyMemberService
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file, injectcontext
from Babylon.utils.credentials import pass_azure_token
<<<<<<< HEAD
=======

>>>>>>> cb4637b4 (remove querytype)

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_azure_token("graph")
@argument("group_id", type=str)
def get_all(azure_token: str, group_id: str) -> CommandResponse:
    """
    Get members of a group in active directory
    https://learn.microsoft.com/en-us/graph/api/group-post-members
    """
    service = AzureDirectoyMemberService(azure_token=azure_token)
    response = service.get_all(group_id=group_id)
    return CommandResponse.success(response, verbose=True)
