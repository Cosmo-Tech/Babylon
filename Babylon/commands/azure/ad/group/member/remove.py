import logging

from click import option
from click import command
<<<<<<< HEAD
<<<<<<< HEAD

=======
from Babylon.utils.typing import QueryType
>>>>>>> 53b0a6f8 (add injectcontext)
=======

>>>>>>> cb4637b4 (remove querytype)
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.credentials import pass_azure_token
from Babylon.commands.azure.ad.services.member import AzureDirectoyMemberService

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_azure_token("graph")
@option("--gi", "--group-id", "group_id", type=str, required=True, help="Group Id Azure Directory")
@option("--pi", "--principal-id", "principal_id", type=str, required=True, help="Principal Id Azure Directory")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
def remove(azure_token: str, group_id: str, principal_id: str, force_validation: bool = False) -> CommandResponse:
    """
    Remove a member from a group in active directory
    """
    if not force_validation and not confirm_deletion("member", principal_id):
        return CommandResponse.fail()
    service = AzureDirectoyMemberService(azure_token=azure_token)
    service.remove(group_id=group_id, principal_id=principal_id)
    return CommandResponse.success()
