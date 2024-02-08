import logging

from typing import Any
from click import command
from click import argument
from click import option
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("report_id", type=QueryType())
@inject_context_with_resource({"powerbi": ["workspace"]})
def delete(
    context: Any,
    powerbi_token: str,
    report_id: str,
    workspace_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a powerbi report in the current workspace
    """
    service = AzurePowerBIReportService(
        powerbi_token=powerbi_token, state=context
    )
    service.delete(
        workspace_id=workspace_id,
        report_id=report_id,
        force_validation=force_validation,
    )
    return CommandResponse.success()
