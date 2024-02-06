import logging

from click import command, option
from Babylon.commands.azure.ad.group.member.service.api import (
    AzureDirectoyMemberService,
)
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_azure_token("graph")
@option(
    "--gi",
    "--group-id",
    "group_id",
    type=QueryType(),
    required=True,
    help="Group Id Azure Directory",
)
@option(
    "--pi",
    "--principal-id",
    "principal_id",
    type=QueryType(),
    required=True,
    help="Principal Id Azure Directory",
)
def add(
    azure_token: str,
    group_id: str,
    principal_id: str,
) -> CommandResponse:
    """
    Add a member in a group in active directory
    https://learn.microsoft.com/en-us/graph/api/group-post-members
    """
    apiMember = AzureDirectoyMemberService(azure_token=azure_token)
    apiMember.add(group_id=group_id, principal_id=principal_id)
    return CommandResponse.success()
