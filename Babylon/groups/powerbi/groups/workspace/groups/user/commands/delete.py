import logging
from typing import Optional

from azure.core.credentials import AccessToken
from click import Context
from click import argument
from click import command
from click import option
from click import pass_context

from ........utils.decorators import require_deployment_key
from ........utils.interactive import confirm_deletion
from ........utils.typing import QueryType
from ........utils.response import CommandResponse
from ........utils.request import oauth_request

logger = logging.getLogger("Babylon")


@command()
@pass_context
@option("-w", "--workspace", "override_workspace_id", type=QueryType())
@argument("identifier", type=QueryType())
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
@require_deployment_key("powerbi_workspace_id", required=False)
def delete(
    ctx: Context,
    powerbi_workspace_id: str,
    override_workspace_id: Optional[str],
    identifier: str,
    force_validation: Optional[bool] = False,
) -> CommandResponse:
    """Delete IDENTIFIER from the power bi workspace"""
    access_token = ctx.find_object(AccessToken).token
    workspace_id = override_workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    url_users = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users/{identifier}'
    if not force_validation and not confirm_deletion("user", identifier):
        return CommandResponse.fail()
    response = oauth_request(url=url_users, access_token=access_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"{identifier} was successfully removed from workspace {workspace_id}")
    return CommandResponse()
