import logging
import pathlib

from typing import Any, Optional
from click import command
from click import argument
from click import option
from click import Path
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService
from Babylon.utils.response import CommandResponse
<<<<<<< HEAD
from Babylon.utils.decorators import retrieve_state, injectcontext
=======
from Babylon.utils.decorators import retrieve_state, wrapcontext
>>>>>>> cc0b634d (add new state to powerbi)
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@option(
    "-o",
    "--output",
    "output_folder",
    type=Path(path_type=pathlib.Path),
    default="powerbi",
    help="Output folder",
)
<<<<<<< HEAD
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@argument("report_id", type=str)
=======
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@argument("report_id", type=QueryType())
>>>>>>> cc0b634d (add new state to powerbi)
@retrieve_state
def download(
    state: Any,
    powerbi_token: str,
    report_id: str,
    workspace_id: str,
    output_folder: Optional[pathlib.Path],
) -> CommandResponse:
    """
    Download a report in the current workspace
    """
<<<<<<< HEAD
    service_state = state['services']
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=service_state)
    response = service.download(workspace_id=workspace_id, report_id=report_id, output_folder=output_folder)
=======
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=state)
    response = service.download(
        workspace_id=workspace_id, report_id=report_id, output_folder=output_folder
    )
>>>>>>> cc0b634d (add new state to powerbi)
    return CommandResponse.success({"file": response})
