from logging import getLogger

from click import command
from click import option

from .....utils.credentials import pass_azure_token
from .....utils.decorators import output_to_file
from .....utils.decorators import require_platform_key
from .....utils.decorators import timing_decorator
from .....utils.request import oauth_request
from .....utils.response import CommandResponse
from .....utils.typing import QueryType

logger = getLogger("Babylon")


@command()
@timing_decorator
@require_platform_key("api_url")
@pass_azure_token("csm_api")
@option("--organization", "organization_id", type=QueryType(), default="%deploy%organization_id")
@option("--workspace", "workspace_id", type=QueryType(), default="%deploy%workspace_id")
@output_to_file
def get(api_url: str, azure_token: str, organization_id: str, workspace_id: str) -> CommandResponse:
    """
    Update workspace users RBAC access
    """

    response = oauth_request(f"{api_url}/organizations/{organization_id}/workspaces/{workspace_id}/security",
                             azure_token,
                             type="GET")
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    return CommandResponse.success(workspace, verbose=True)
