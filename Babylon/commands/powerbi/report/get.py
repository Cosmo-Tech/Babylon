import logging

from typing import Any
from click import option
from click import command
from click import argument

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService
from Babylon.utils.decorators import (
    output_to_file,
    retrieve_state,
    injectcontext,
)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@argument("report_id", type=str)
@retrieve_state
def get(
    state: Any,
    powerbi_token: str,
    report_id: str,
    workspace_id: str,
) -> CommandResponse:
    """
    Get info from a powerbi report of a workspace
    """
    service_state = state['services']
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=service_state)
    response = service.get(workspace_id=workspace_id, report_id=report_id)
    return CommandResponse.success(response, verbose=True)
