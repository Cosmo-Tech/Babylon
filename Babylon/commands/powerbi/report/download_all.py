import logging
import pathlib
from typing import Any

from click import Path, command, option

from Babylon.commands.powerbi.report.service.powerbi_report_api_svc import AzurePowerBIReportService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_powerbi_token()
@option("-w", "--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option(
    "-o",
    "--output",
    "output_folder",
    help="Output folder",
    type=Path(path_type=pathlib.Path),
    default="powerbi",
)
@retrieve_state
def download_all(state: Any, powerbi_token: str, workspace_id: str, output_folder: pathlib.Path) -> CommandResponse:
    """
    Download all reports from a workspace
    """
    service_state = state["services"]
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=service_state)
    service.download_all(workspace_id=workspace_id, output_folder=output_folder)
    return CommandResponse.success()
