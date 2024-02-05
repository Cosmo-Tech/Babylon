import logging
import pathlib

from typing import Any
from click import command
from click import option
from click import Path
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option(
    "-o",
    "--output",
    "output_folder",
    help="Output folder",
    type=Path(path_type=pathlib.Path),
    default="powerbi",
)
@inject_context_with_resource({"powerbi": ["workspace"]})
def download_all(
    context: Any, powerbi_token: str, workspace_id: str, output_folder: pathlib.Path
) -> CommandResponse:
    """
    Download all reports from a workspace
    """
    api_powerbi_report = AzurePowerBIReportService(
        powerbi_token=powerbi_token, state=context
    )
    macro = api_powerbi_report.download_all(
        workspace_id=workspace_id, output_folder=output_folder
    )
    return CommandResponse.success(macro.env.get_data(["reports", "data"]))
