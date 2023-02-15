import logging
from typing import Optional

from click import command
from click import argument
from click import option

from ......utils.decorators import require_deployment_key
from ......utils.request import oauth_request
from ......utils.response import CommandResponse
from ......utils.typing import QueryType
from ......utils.interactive import confirm_deletion
from ......utils.credentials import get_azure_token

logger = logging.getLogger("Babylon")


@command()
@require_deployment_key("powerbi_workspace_id", required=False)
@argument("report_id", type=QueryType())
@option("-w", "--workspace", "workspace_id", help="PowerBI workspace ID")
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
def delete(powerbi_workspace_id: str,
           report_id: str,
           workspace_id: Optional[str] = None,
           force_validation: bool = False) -> CommandResponse:
    """Delete a powerbi report in the current workspace"""
    workspace_id = workspace_id or powerbi_workspace_id
    if not workspace_id:
        logger.error("A workspace id is required either in your config or with parameter '-w'")
        return CommandResponse.fail()
    if not force_validation and not confirm_deletion("report", report_id):
        return CommandResponse.fail()
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
    response = oauth_request(url=urls_reports, access_token=get_azure_token("powerbi"), type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Report id {report_id} successfully deleted.")
    return CommandResponse.success()
