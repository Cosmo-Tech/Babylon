import logging
from typing import Any

from click import Choice, argument, command, option

from Babylon.commands.powerbi.report.service.powerbi_report_api_svc import AzurePowerBIReportService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import (
    injectcontext,
    output_to_file,
    retrieve_state,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
@option(
    "--report-type",
    "report_type",
    type=Choice(["scenario_view", "dashboard_view"]),
    help="Report Type",
)
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@argument("report_id", type=str)
@retrieve_state
def pages(
    state: Any,
    powerbi_token: str,
    report_id: str,
    report_type: str,
    workspace_id: str,
) -> CommandResponse:
    """
    Get info from a powerbi report of a workspace
    """
    service_state = state["services"]
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=service_state)
    service.pages(workspace_id=workspace_id, report_id=report_id, report_type=report_type)
    return CommandResponse.success()
