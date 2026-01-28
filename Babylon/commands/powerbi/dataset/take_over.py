import logging
from typing import Any

from click import argument, command, option

from Babylon.commands.powerbi.dataset.services.powerbi_api_svc import AzurePowerBIDatasetService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@option("-w", "--workspace-id", "workspace_id", type=str, help="PowerBI workspace ID")
@argument("dataset_id", type=str)
@retrieve_state
def take_over(
    state: Any,
    powerbi_token: str,
    workspace_id: str,
    dataset_id: str,
) -> CommandResponse:
    """
    Take ownership of a powerbi dataset in the current workspace
    """
    service_state = state["services"]
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=service_state)
    service.take_over(workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse.success()
