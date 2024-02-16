from click import argument, command
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, retrieve_state, timing_decorator
from Babylon.services.security.solution_security_service import SolutionSecurityService


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@output_to_file
@argument("identity_id", type=str)
@retrieve_state
def remove_control_access(state: dict, azure_token: str, identity_id: str) -> CommandResponse:
    """
    Remove the specified access from the given Organization Solution
    """
    service_state = state["services"]
    service = SolutionSecurityService(azure_token=azure_token, state=service_state)
    response = service.remove_control_access(identity_id)
    return CommandResponse.success(response, verbose=True)
