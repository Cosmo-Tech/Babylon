import logging

from click import command
from click import option
from click import argument

from ......utils.interactive import confirm_deletion
from ......utils.typing import QueryType
from ......utils.response import CommandResponse
from ......utils.request import oauth_request
from ......utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@argument("workspace_id", type=QueryType())
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
def delete(azure_token: str, workspace_id: str, force_validation: bool) -> CommandResponse:
    """Delete workspace from Power Bi APP"""
    if not force_validation and not confirm_deletion("Power Bi Workspace", workspace_id):
        return CommandResponse.fail()
    url_delete = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}'
    response = oauth_request(url=url_delete, access_token=azure_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"{workspace_id} was successfully removed from power bi app")
    return CommandResponse.success()
