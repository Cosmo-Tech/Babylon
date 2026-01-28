import logging
from typing import Any

from click import argument, command, option

from Babylon.commands.powerbi.dataset.services.powerbi_api_svc import AzurePowerBIDatasetService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@argument("dataset_id", type=str)
@option("-w", "--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
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
    service_state = state["services"]
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=service_state)
    response = service.get(workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse.success(response, verbose=True)
