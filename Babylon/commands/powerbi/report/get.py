import logging
from typing import Optional

from click import command
from click import argument
from click import option
from rich.pretty import pretty_repr

from ....utils.decorators import require_deployment_key
from ....utils.decorators import output_to_file
from ....utils.request import oauth_request
from ....utils.response import CommandResponse
from ....utils.typing import QueryType
from ....utils.credentials import pass_azure_token

logger = logging.getLogger("Babylon")


@command()
@pass_azure_token("powerbi")
@argument("report_id", type=QueryType())
@option("-w",
        "--workspace",
        "workspace_id",
        help="PowerBI workspace ID",
        type=QueryType(),
        default="%deploy%powerbi_workspace_id")
@output_to_file
def get(azure_token: str, report_id: str, workspace_id: str) -> CommandResponse:
    """Get info from a powerbi report of a workspace"""
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
    response = oauth_request(urls_reports, azure_token)
    if response is None:
        return CommandResponse.fail()
    output_data = response.json()
    logger.info(pretty_repr(output_data))
    return CommandResponse.success(output_data)
