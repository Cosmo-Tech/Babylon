import logging
from typing import Optional

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import Context
from click import option

from ......utils.decorators import require_deployment_key
from ......utils.decorators import output_to_file
from ......utils.response import CommandResponse
from ......utils.request import oauth_request

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id", required=False)
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
@output_to_file
def get_all(ctx: Context, powerbi_workspace_id: str, workspace_id: Optional[str] = None) -> CommandResponse:
    """Get a list of all powerbi datasets in the current workspace"""
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    access_token = ctx.find_object(AccessToken).token
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    response = oauth_request(url, access_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.get("value")
    return CommandResponse(data=output_data)
