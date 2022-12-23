import logging
from typing import Optional

from azure.core.credentials import AccessToken
from click import command
from click import pass_context
from click import argument
from click import Context
from click import option

from ......utils.decorators import require_deployment_key
from ......utils.decorators import output_to_file
from ......utils.request import oauth_request
from ......utils.response import CommandResponse
from ......utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_context
@require_deployment_key("powerbi_workspace_id", required=False)
@argument("report_id", type=QueryType())
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
@output_to_file
def get(ctx: Context, powerbi_workspace_id: str, report_id: str, workspace_id: Optional[str] = None) -> CommandResponse:
    """Get info from a powerbi report of a workspace"""
    access_token = ctx.find_object(AccessToken).token
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
    response = oauth_request(url=urls_reports, access_token=access_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(output_data)
    return CommandResponse(data=output_data)