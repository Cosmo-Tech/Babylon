import logging
from typing import Any

from click import command
from click import argument
from click import option
from Babylon.commands.powerbi.dataset.service.api import AzurePowerBIDatasetService

from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", type=QueryType(), help="PowerBI workspace ID")
@argument("dataset_id", type=QueryType())
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
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=state)
    service.take_over(workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse.success()
