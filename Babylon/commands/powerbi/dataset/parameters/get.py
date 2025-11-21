import logging
from typing import Any, Optional

from click import argument, command, option

from Babylon.commands.powerbi.dataset.services.powerbi_params_svc import AzurePowerBIParamsService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=str, help="PowerBI workspace ID")
@argument("dataset_id", type=str)
@option("--workspace-id", "workspace_id", type=str, help="PowerBI workspace ID")
@retrieve_state
def get(
    state: Any,
    powerbi_token: str,
    dataset_id: str,
    workspace_id: Optional[str] = None,
) -> CommandResponse:
    """
    Get parameters of a given dataset
    """
    service_state = state["services"]
    service = AzurePowerBIParamsService(powerbi_token=powerbi_token, state=service_state)
    response = service.get(workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse.success(response, verbose=True)
