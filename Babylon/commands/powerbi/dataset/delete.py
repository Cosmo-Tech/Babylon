import logging
from typing import Any, Optional

from click import command
from click import option
from click import argument
from Babylon.commands.powerbi.dataset.service.api import AzurePowerBIDatasetService
<<<<<<< HEAD
<<<<<<< HEAD
from Babylon.utils.decorators import retrieve_state, injectcontext
=======
from Babylon.utils.decorators import retrieve_state, wrapcontext
>>>>>>> cc0b634d (add new state to powerbi)
=======
from Babylon.utils.decorators import retrieve_state, injectcontext
>>>>>>> 53b0a6f8 (add injectcontext)
from Babylon.utils.response import CommandResponse

from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
<<<<<<< HEAD
@argument("dataset_id", type=str)
=======
@argument("dataset_id", type=QueryType())
>>>>>>> cc0b634d (add new state to powerbi)
@retrieve_state
def delete(
    state: Any,
    powerbi_token: str,
    dataset_id: str,
    workspace_id: Optional[str] = None,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a powerbi dataset in the current workspace
    """
<<<<<<< HEAD
    service_state = state['services']
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=service_state)
=======
    service = AzurePowerBIDatasetService(powerbi_token=powerbi_token, state=state)
>>>>>>> cc0b634d (add new state to powerbi)
    response = service.delete(
        workspace_id=workspace_id,
        force_validation=force_validation,
        dataset_id=dataset_id,
    )
    return CommandResponse.success(response)
