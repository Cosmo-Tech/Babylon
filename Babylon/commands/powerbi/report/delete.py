import logging

from click import command
from click import argument
from click import option

from ....utils.request import oauth_request
from ....utils.response import CommandResponse
from ....utils.typing import QueryType
from ....utils.interactive import confirm_deletion
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
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
def delete(azure_token: str, report_id: str, workspace_id: str, force_validation: bool = False) -> CommandResponse:
    """Delete a powerbi report in the current workspace"""
    if not force_validation and not confirm_deletion("report", report_id):
        return CommandResponse.fail()
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
    response = oauth_request(url=urls_reports, access_token=azure_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Report id {report_id} successfully deleted.")
    return CommandResponse.success()
