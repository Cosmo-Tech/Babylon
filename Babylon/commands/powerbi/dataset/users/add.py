import logging
from typing import Any

from click import argument, command, option

from Babylon.commands.powerbi.dataset.services.powerbi_users_svc import AzurePowerBUsersIService
from Babylon.utils.credentials import pass_powerbi_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_powerbi_token()
@option("--workspace-id", "workspace_id", help="PowerBI workspace ID", type=str)
@option("--email", "email", type=str, help="Email valid")
@argument("dataset_id", type=str)
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
    service_state = state["services"]
    service = AzurePowerBUsersIService(powerbi_token=powerbi_token, state=service_state)
    response = service.add(email=email, workspace_id=workspace_id, dataset_id=dataset_id)
    return CommandResponse.success(response.text, verbose=True)
