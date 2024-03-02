import logging

from typing import Any
from click import option
from click import argument
from click import Choice, command

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService
from Babylon.utils.decorators import (
    output_to_file,
    retrieve_state,
<<<<<<< HEAD
<<<<<<< HEAD
    injectcontext,
=======
    wrapcontext,
>>>>>>> cc0b634d (add new state to powerbi)
=======
    injectcontext,
>>>>>>> 53b0a6f8 (add injectcontext)
)

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
<<<<<<< HEAD
<<<<<<< HEAD
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@argument("report_id", type=str)
=======
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@argument("report_id", type=QueryType())
>>>>>>> cc0b634d (add new state to powerbi)
=======
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@argument("report_id", type=str)
>>>>>>> cb4637b4 (remove querytype)
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
<<<<<<< HEAD
    service_state = state['services']
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=service_state)
    service.pages(workspace_id=workspace_id, report_id=report_id, report_type=report_type)
=======
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=state)
    service.pages(
        workspace_id=workspace_id, report_id=report_id, report_type=report_type
    )
>>>>>>> cc0b634d (add new state to powerbi)
    return CommandResponse.success()
