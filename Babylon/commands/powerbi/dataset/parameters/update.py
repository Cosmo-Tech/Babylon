import logging
from typing import Any, Optional

from click import argument, command, option

from Babylon.commands.powerbi.dataset.services.powerbi_params_svc import AzurePowerBIParamsService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@option(
    "--parameter",
    "params",
    type=(str, str),
    multiple=True,
    required=True,
    help="Report parameter",
)
@option("-w", "--workspace-id", "workspace_id", type=str, help="PowerBI workspace ID")
@argument("dataset_id", type=str)
@retrieve_state
def update(
    state: Any,
    powerbi_token: str,
    dataset_id: str,
    params: list[tuple[str, str]],
    workspace_id: Optional[str] = None,
) -> CommandResponse:
    """
    Update parameters of a given dataset
    """
    service_state = state["services"]
    service = AzurePowerBIParamsService(powerbi_token=powerbi_token, state=service_state)
    service.update(workspace_id=workspace_id, params=params, dataset_id=dataset_id)
    return CommandResponse.success()
