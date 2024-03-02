import logging

from typing import Any, Optional
from click import command
from click import argument
from click import option
from Babylon.commands.powerbi.dataset.parameters.service.api import AzurePowerBIParamsService
<<<<<<< HEAD
<<<<<<< HEAD
from Babylon.utils.decorators import retrieve_state, injectcontext
=======
from Babylon.utils.decorators import retrieve_state, wrapcontext
>>>>>>> cc0b634d (add new state to powerbi)
=======
from Babylon.utils.decorators import retrieve_state, injectcontext
>>>>>>> 53b0a6f8 (add injectcontext)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse

from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_powerbi_token()
<<<<<<< HEAD
<<<<<<< HEAD
@option("--workspace-id", "workspace_id", type=str, help="PowerBI workspace ID")
@argument("dataset_id", type=str)
=======
@option("--workspace-id", "workspace_id", type=QueryType(), help="PowerBI workspace ID")
@argument("dataset_id", type=QueryType())
>>>>>>> cc0b634d (add new state to powerbi)
=======
@option("--workspace-id", "workspace_id", type=str, help="PowerBI workspace ID")
@argument("dataset_id", type=str)
>>>>>>> cb4637b4 (remove querytype)
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
<<<<<<< HEAD
    service_state = state['services']
    service = AzurePowerBIParamsService(powerbi_token=powerbi_token, state=service_state)
=======
    service = AzurePowerBIParamsService(powerbi_token=powerbi_token, state=state)
>>>>>>> cc0b634d (add new state to powerbi)
    response = service.get(workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse.success(response, verbose=True)
