import logging

from click import option
from click import command
from typing import Any, Optional
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import output_to_file, retrieve_state, wrapcontext

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@output_to_file
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(
    state: Any, powerbi_token: str, workspace_id: str, filter: Optional[str] = None
) -> CommandResponse:
    """
    Get info from every powerbi reports of a workspace
    """
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=state)
    response = service.get_all(workspace_id=workspace_id, filter=filter)
    return CommandResponse.success(response, verbose=True)
