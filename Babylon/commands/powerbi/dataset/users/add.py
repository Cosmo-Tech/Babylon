import logging

from typing import Any
from click import option
from click import argument, command
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.commands.powerbi.dataset.users.service.api import AzurePowerBUsersIService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=QueryType())
@option("--email", "email", type=QueryType(), help="Email valid")
@argument("dataset_id", type=QueryType())
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
    service = AzurePowerBUsersIService(
        powerbi_token=powerbi_token, state=state
    )
    response = service.add(email=email, workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse.success(response.text, verbose=True)
