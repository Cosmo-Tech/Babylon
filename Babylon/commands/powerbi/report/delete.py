import logging
from typing import Any

from click import argument, command, option

from Babylon.commands.powerbi.report.service.powerbi_report_api_svc import AzurePowerBIReportService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("report_id", type=str)
@retrieve_state
def delete(
    state: Any,
    powerbi_token: str,
    report_id: str,
    workspace_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a powerbi report in the current workspace
    """
    service_state = state["services"]
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=service_state)
    service.delete(
        workspace_id=workspace_id,
        report_id=report_id,
        force_validation=force_validation,
    )
    return CommandResponse.success()
