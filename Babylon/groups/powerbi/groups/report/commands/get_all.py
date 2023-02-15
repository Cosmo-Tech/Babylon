import logging
from typing import Optional

from click import command
from click import option
from rich.pretty import pretty_repr

from ......utils.decorators import require_deployment_key
from ......utils.decorators import output_to_file
from ......utils.request import oauth_request
from ......utils.response import CommandResponse
from ......utils.credentials import get_azure_token

logger = logging.getLogger("Babylon")


@command()
@require_deployment_key("powerbi_workspace_id", required=False)
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
@output_to_file
def get_all(powerbi_workspace_id: str, workspace_id: Optional[str] = None) -> CommandResponse:
    """Get info from every powerbi reports of a workspace"""
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
    response = oauth_request(urls_reports, get_azure_token("powerbi"))
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get("value")
    logger.info("\n".join([pretty_repr(data) for data in output_data]))
    return CommandResponse.success(output_data)
