import logging
from typing import Any

from click import command, option

from Babylon.commands.powerbi.report.service.powerbi_report_api_svc import AzurePowerBIReportService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
@option("-w", "--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@retrieve_state
def get_all(state: Any, powerbi_token: str, workspace_id: str) -> CommandResponse:
    """
    Get info from every powerbi reports of a workspace
    """
    service_state = state["services"]
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=service_state)
    response = service.get_all(workspace_id=workspace_id)
    return CommandResponse.success(response, verbose=True)
