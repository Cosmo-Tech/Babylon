import logging
from typing import Optional

from click import command
from click import option
from rich.pretty import pretty_repr

from ....utils.decorators import require_deployment_key
from ....utils.decorators import output_to_file
from ....utils.request import oauth_request
from ....utils.response import CommandResponse
from ....utils.credentials import pass_azure_token
from ....utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@option("-w",
        "--workspace",
        "workspace_id",
        help="PowerBI workspace ID",
        type=QueryType(),
        default="%deploy%powerbi_workspace_id")
@output_to_file
def get_all(azure_token: str, workspace_id: Optional[str] = None) -> CommandResponse:
    """Get info from every powerbi reports of a workspace"""
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
    response = oauth_request(urls_reports, azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json().get("value")
    logger.info("\n".join([pretty_repr(data) for data in output_data]))
    return CommandResponse.success(output_data)
