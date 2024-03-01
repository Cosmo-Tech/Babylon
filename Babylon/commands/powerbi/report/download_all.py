import logging
import pathlib

from typing import Any
from click import Path
<<<<<<< HEAD
from click import option
from click import command
=======
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService
from Babylon.utils.credentials import pass_powerbi_token
<<<<<<< HEAD
from Babylon.utils.decorators import retrieve_state, wrapcontext
>>>>>>> cc0b634d (add new state to powerbi)
=======
from Babylon.utils.decorators import retrieve_state, injectcontext
>>>>>>> 53b0a6f8 (add injectcontext)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option(
    "-o",
    "--output",
    "output_folder",
    help="Output folder",
    type=Path(path_type=pathlib.Path),
    default="powerbi",
)
@retrieve_state
<<<<<<< HEAD
def download_all(state: Any, powerbi_token: str, workspace_id: str, output_folder: pathlib.Path) -> CommandResponse:
    """
    Download all reports from a workspace
    """
    service_state = state['services']
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=service_state)
    service.download_all(workspace_id=workspace_id, output_folder=output_folder)
    return CommandResponse.success()
=======
def download_all(
    state: Any, powerbi_token: str, workspace_id: str, output_folder: pathlib.Path
) -> CommandResponse:
    """
    Download all reports from a workspace
    """
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=state)
    macro = service.download_all(workspace_id=workspace_id, output_folder=output_folder)
    return CommandResponse.success(macro.env.get_data(["reports", "data"]))
>>>>>>> cc0b634d (add new state to powerbi)
