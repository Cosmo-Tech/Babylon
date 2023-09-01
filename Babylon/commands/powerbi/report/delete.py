import logging

from typing import Any
from click import command
from click import argument
from click import option
from Babylon.utils.messages import SUCCESS_DELETED
from Babylon.utils.request import oauth_request
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@pass_powerbi_token()
@option("--workspace","workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("-D", "force_validation", is_flag=True, help="Delete on force mode")
@argument("report_id", type=QueryType())
@inject_context_with_resource({"powerbi": ['workspace']})
def delete(context: Any,
           powerbi_token: str,
           report_id: str,
           workspace_id: str,
           force_validation: bool = False) -> CommandResponse:
    """
    Delete a powerbi report in the current workspace
    """
    report_id = report_id or context['powerbi_workspace']['report_id']

    if not force_validation and not confirm_deletion("report", report_id):
        return CommandResponse.fail()
    urls_reports = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}"
    response = oauth_request(url=urls_reports, access_token=powerbi_token, type="DELETE")
    if response is None:
        return CommandResponse.fail()
    logger.info(SUCCESS_DELETED("report", report_id))
    return CommandResponse.success()
