import logging
import pathlib

from typing import Any, Optional
from click import command
from click import argument
from click import option
from click import Path
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@option(
    "-o",
    "--output",
    "output_folder",
    type=Path(path_type=pathlib.Path),
    default="powerbi",
    help="Output folder",
)
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@argument("report_id", type=QueryType())
@inject_context_with_resource({"powerbi": ["workspace"]})
def download(
    context: Any,
    powerbi_token: str,
    report_id: str,
    workspace_id: str,
    output_folder: Optional[pathlib.Path],
) -> CommandResponse:
    """
    Download a report in the current workspace
    """
    api_powerbi_report = AzurePowerBIReportService(
        powerbi_token=powerbi_token, state=context
    )
    response = api_powerbi_report.download(
        workspace_id=workspace_id, report_id=report_id, output_folder=output_folder
    )
    return CommandResponse.success({"file": response})
