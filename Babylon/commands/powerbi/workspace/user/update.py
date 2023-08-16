import logging

from typing import Any, Optional
from click import Choice
from click import argument
from click import command
from click import option
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.request import oauth_request
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@pass_powerbi_token()
@option("-w", "--workspace", "workspace_id", type=QueryType())
@argument("email", type=QueryType())
@argument("type", type=Choice(["App", "Group", "User", "None"], case_sensitive=False))
@argument("right", type=Choice(["Admin", "Contributor", "Member", "Viewer", "None"], case_sensitive=False))
@inject_context_with_resource({"powerbi": ['workspace']})
def update(
    context: Any,
    powerbi_token: str,
    workspace_id: Optional[str],
    email: str,
    type: str,
    right: str,
) -> CommandResponse:
    """
    Updates an existing user in the power bi workspace using the following information:

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
  None        : No access to content
  """
    workspace_id = workspace_id or context['powerbi_workspace']['id']
    url_users = f'https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users'
    body = {
        "identifier": email,
        "groupUserAccessRight": right,
        "principalType": type,
    }
    response = oauth_request(url_users, powerbi_token, json=body, type="PUT")
    if response is None:
        return CommandResponse.fail()
    logger.info("Successfully updated")
    return CommandResponse.success()
