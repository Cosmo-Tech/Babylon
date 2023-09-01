import logging

from typing import Any, Optional
from click import argument
from click import command
from click import option
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@pass_powerbi_token()
@option("--workspace", "workspace_id", type=QueryType())
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
@argument("email", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def delete(
    context: Any,
    powerbi_token: str,
    workspace_id: Optional[str],
    email: str,
    force_validation: Optional[bool] = False,
) -> CommandResponse:
    """
    Delete IDENTIFIER from the power bi workspace
    """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    url_users = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users/{email}'
    if not force_validation and not confirm_deletion("user", email):
        return CommandResponse.fail()
    response = oauth_request(url_users, powerbi_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info("Successfully removed")
    return CommandResponse.success()
