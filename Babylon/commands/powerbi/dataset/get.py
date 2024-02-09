import logging

from typing import Any
from click import command
from click import option
from click import argument
from Babylon.commands.powerbi.dataset.service.api import AzurePowerBIDatasetService
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@argument("dataset_id", type=QueryType())
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@output_to_file
@retrieve_state
def get(
    state: Any,
    powerbi_token: str,
    workspace_id: str,
    dataset_id: str,
) -> CommandResponse:
    """
    Get a powerbi dataset in the current workspace
    """
    service_state = state['services']
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=service_state)
    response = service.get(workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse.success(response, verbose=True)
