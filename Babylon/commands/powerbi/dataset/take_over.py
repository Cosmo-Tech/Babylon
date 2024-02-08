import logging
from typing import Any

from click import command
from click import argument
from click import option
from Babylon.commands.powerbi.dataset.service.api import AzurePowerBIDatasetService

<<<<<<< HEAD
from Babylon.utils.decorators import retrieve_state, injectcontext
=======
from Babylon.utils.decorators import retrieve_state, wrapcontext
>>>>>>> cc0b634d (add new state to powerbi)
from Babylon.utils.response import CommandResponse

from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
<<<<<<< HEAD
@option("--workspace-id", "workspace_id", type=str, help="PowerBI workspace ID")
@argument("dataset_id", type=str)
=======
@option("--workspace-id", "workspace_id", type=QueryType(), help="PowerBI workspace ID")
@argument("dataset_id", type=QueryType())
>>>>>>> cc0b634d (add new state to powerbi)
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
<<<<<<< HEAD
    service_state = state['services']
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=service_state)
=======
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=state)
>>>>>>> cc0b634d (add new state to powerbi)
    service.take_over(workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse.success()
