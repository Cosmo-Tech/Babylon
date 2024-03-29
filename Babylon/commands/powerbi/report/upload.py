import logging
import pathlib

from typing import Any
from click import Path
from click import option
from click import Choice, command

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.commands.powerbi.report.service.powerbi_report_api_svc import AzurePowerBIReportService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_powerbi_token()
@option(
    "--file",
    "pbix_filename",
    type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
    required=True,
    help="Your report file",
)
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option(
    "--override",
    "override",
    is_flag=True,
    help="override reports in case of name conflict",
)
@option("--name", "report_name", type=str, help="Report name")
@option(
    "--type",
    "report_type",
    type=Choice(["scenario_view", "dashboard_view"]),
    required=True,
    help="Report type",
)
@retrieve_state
def upload(
    state: Any,
    powerbi_token: str,
    pbix_filename: pathlib.Path,
    workspace_id: str,
    report_name: str,
    report_type: str,
    override: bool = False,
) -> CommandResponse:
    """
    Publish the given pbxi file to the PowerBI workspace
    """
    service_state = state['services']
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=service_state)
    service.upload(
        workspace_id=workspace_id,
        pbix_filename=pbix_filename,
        report_name=report_name,
        report_type=report_type,
        override=override,
    )
    return CommandResponse.success()
