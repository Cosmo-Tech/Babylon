import logging

from typing import Any
from click import option
from click import argument
from click import Choice, command
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService
from Babylon.utils.decorators import (
    inject_context_with_resource,
    output_to_file,
    wrapcontext,
)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@output_to_file
@pass_powerbi_token()
@option(
    "--report-type",
    "report_type",
    type=Choice(["scenario_view", "dashboard_view"]),
    help="Report Type",
)
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@argument("report_id", type=QueryType())
@inject_context_with_resource({"powerbi": ["workspace"]})
def pages(
    context: Any,
    powerbi_token: str,
    report_id: str,
    report_type: str,
    workspace_id: str,
) -> CommandResponse:
    """
    Get info from a powerbi report of a workspace
    """
    service = AzurePowerBIReportService(
        powerbi_token=powerbi_token, state=context
    )
    service.pages(
        workspace_id=workspace_id, report_id=report_id, report_type=report_type
    )
    return CommandResponse.success()
