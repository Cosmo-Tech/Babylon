import logging

from click import command, option
from Babylon.commands.azure.ad.services.member import AzureDirectoyMemberService
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse

from Babylon.utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_azure_token("graph")
@option(
    "--gi",
    "--group-id",
    "group_id",
    type=str,
    required=True,
    help="Group Id Azure Directory",
)
@option(
    "--pi",
    "--principal-id",
    "principal_id",
    type=str,
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
    service = AzureDirectoyMemberService(azure_token=azure_token)
    service.add(group_id=group_id, principal_id=principal_id)
    return CommandResponse.success()
