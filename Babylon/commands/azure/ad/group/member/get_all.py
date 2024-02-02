import logging

from click import command
from click import argument
from Babylon.commands.azure.ad.group.member.service.api import AzureDirectoyMemberService
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file, wrapcontext
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@output_to_file
@pass_azure_token("graph")
@argument("group_id", type=QueryType())
def get_all(azure_token: str, group_id: str) -> CommandResponse:
    """
    Get members of a group in active directory
    https://learn.microsoft.com/en-us/graph/api/group-post-members
    """
    apiMember = AzureDirectoyMemberService()
    response = apiMember.get_all(group_id=group_id, azure_token=azure_token)
    return CommandResponse.success(response, verbose=True)
