import logging

from typing import Any
from click import command
from click import argument
from click import option
from Babylon.commands.powerbi.report.service.powerbi_report_api_svc import AzurePowerBIReportService
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.response import CommandResponse

from Babylon.utils.credentials import pass_powerbi_token

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
    service_state = state['services']
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=service_state)
    service.delete(
        workspace_id=workspace_id,
        report_id=report_id,
        force_validation=force_validation,
    )
    return CommandResponse.success()
