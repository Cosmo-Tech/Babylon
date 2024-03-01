from typing import Any
from click import command
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.commands.api.solutions.services.security import SolutionSecurityService


@command()
@injectcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@retrieve_state
def get_all(
    state: Any,
    azure_token: str,
) -> CommandResponse:
    """
    Get the Solution security information
    """
    service_state = state["services"]
    service = SolutionSecurityService(azure_token=azure_token, state=service_state)
    response = service.get_security()
    return CommandResponse.success(response, verbose=True)
