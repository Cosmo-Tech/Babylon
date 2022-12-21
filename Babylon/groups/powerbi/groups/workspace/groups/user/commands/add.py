import logging
from typing import Optional

from azure.core.credentials import AccessToken
from click import Choice
from click import Context
from click import argument
from click import command
from click import option
from click import pass_context

from ........utils.decorators import require_deployment_key
from ........utils.typing import QueryType
from ........utils.response import CommandResponse
from ........utils.request import oauth_request

logger = logging.getLogger("Babylon")


@command()
@pass_context
@option("-w", "--workspace", "override_workspace_id", required=False, type=QueryType())
@argument("identifier", type=QueryType())
@argument("principal_type", type=Choice(["App", "Group", "User", "None"], case_sensitive=False))
@argument("group_user_access_right",
          type=Choice(["Admin", "Contributor", "Member", "Viewer", "None"], case_sensitive=False))
@require_deployment_key("powerbi_workspace_id", required=False)
def add(ctx: Context, powerbi_workspace_id: str, override_workspace_id: Optional[str], identifier: str,
        principal_type: str, group_user_access_right: str) -> CommandResponse:
    """Adds a new user to the power bi workspace using the following information:

\b
IDENTIFIER : an identifier for the user to add
\b
PRINCIPAL TYPE
  App   : Used for service principals users (uuid from the service principal from Azure)
  Group : Group principal type (object ID from an AAD group)
  User  : Used for individual users types (user mail address)
  None  : No principal type. Use for whole organization level access
\b
GROUP USER ACCESS RIGHT :
  Admin       : Admin rights
  Member      : Read, reshare and explore rights
  Contributor : Read and explore rights
  Viewer      : Read-only rights
  None        : No access to content"""
    access_token = ctx.find_object(AccessToken).token
    workspace_id = override_workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    url_users = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users'
    body = {
        "identifier": identifier,
        "groupUserAccessRight": group_user_access_right,
        "principalType": principal_type,
    }
    response = oauth_request(url=url_users, access_token=access_token, json_data=body, type="POST")
    if not response:
        return CommandResponse.fail()
    logger.info(f"{identifier} was successfully added as a '{group_user_access_right}' to workspace {workspace_id}")
    return CommandResponse()
