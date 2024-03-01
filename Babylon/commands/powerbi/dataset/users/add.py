import logging

from typing import Any
from click import option
from click import argument, command

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
<<<<<<< HEAD
<<<<<<< HEAD
from Babylon.utils.decorators import retrieve_state, injectcontext
=======
from Babylon.utils.decorators import retrieve_state, wrapcontext
>>>>>>> cc0b634d (add new state to powerbi)
=======
from Babylon.utils.decorators import retrieve_state, injectcontext
>>>>>>> 53b0a6f8 (add injectcontext)
from Babylon.commands.powerbi.dataset.users.service.api import AzurePowerBUsersIService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_powerbi_token()
<<<<<<< HEAD
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option("--email", "email", type=str, help="Email valid")
@argument("dataset_id", type=str)
=======
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("--email", "email", type=QueryType(), help="Email valid")
@argument("dataset_id", type=QueryType())
>>>>>>> cc0b634d (add new state to powerbi)
@retrieve_state
def add(
    state: Any,
    dataset_id: str,
    powerbi_token: str,
    workspace_id: str,
    email: str,
) -> CommandResponse:
    """
    Add user to dataset
    """
<<<<<<< HEAD
    service_state = state['services']
    service = AzurePowerBUsersIService(powerbi_token=powerbi_token, state=service_state)
=======
    service = AzurePowerBUsersIService(
        powerbi_token=powerbi_token, state=state
    )
>>>>>>> cc0b634d (add new state to powerbi)
    response = service.add(email=email, workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse.success(response.text, verbose=True)
