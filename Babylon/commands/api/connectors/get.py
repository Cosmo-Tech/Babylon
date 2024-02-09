from logging import getLogger
from typing import Any
from click import argument
from click import command
from Babylon.commands.api.connectors.service.api import ApiConnectorService
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import output_to_file

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@argument("id", type=str)
@retrieve_state
def get(state: Any, azure_token: str, id: str) -> CommandResponse:
    """Get a registered connector details"""
    service_state = state["services"]
    service = ApiConnectorService(azure_token=azure_token, state=service_state)
    response = service.get(id=id)
    return CommandResponse.success(response, verbose=True)
