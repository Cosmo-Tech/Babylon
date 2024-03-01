import logging

from click import option
from click import command
from typing import Any, Optional
from Babylon.commands.powerbi.report.service.api import AzurePowerBIReportService

from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
<<<<<<< HEAD
<<<<<<< HEAD
from Babylon.utils.decorators import output_to_file, retrieve_state, injectcontext
=======
from Babylon.utils.decorators import output_to_file, retrieve_state, wrapcontext
>>>>>>> cc0b634d (add new state to powerbi)
=======
from Babylon.utils.decorators import output_to_file, retrieve_state, injectcontext
>>>>>>> 53b0a6f8 (add injectcontext)

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
<<<<<<< HEAD
def get_all(state: Any, powerbi_token: str, workspace_id: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get info from every powerbi reports of a workspace
    """
    service_state = state['services']
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=service_state)
=======
def get_all(
    state: Any, powerbi_token: str, workspace_id: str, filter: Optional[str] = None
) -> CommandResponse:
    """
    Get info from every powerbi reports of a workspace
    """
    service = AzurePowerBIReportService(powerbi_token=powerbi_token, state=state)
>>>>>>> cc0b634d (add new state to powerbi)
    response = service.get_all(workspace_id=workspace_id, filter=filter)
    return CommandResponse.success(response, verbose=True)
