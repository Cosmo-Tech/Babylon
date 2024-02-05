import logging

from typing import Any, Optional
from click import command
from click import option
from Babylon.commands.powerbi.dataset.service.api import AzurePowerBIDatasetService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@output_to_file
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("--filter", "filter", help="Filter response with a jmespath query")
@inject_context_with_resource({"powerbi": ["workspace"]})
def get_all(
    context: Any, powerbi_token: str, workspace_id: str, filter: Optional[str] = None
) -> CommandResponse:
    """Get a list of all powerbi datasets in the current workspace"""
    api_powerbi = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=context)
    response = api_powerbi.get_all(workspace_id=workspace_id)
    return CommandResponse.success(response, verbose=True)
