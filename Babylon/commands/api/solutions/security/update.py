import json
from click import argument, option, command
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, retrieve_state
from Babylon.commands.api.solutions.services.solutions_security_svc import SolutionSecurityService


@command()
@injectcontext()
@pass_azure_token("csm_api")
@argument("identity_id", type=str)
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@output_to_file
@retrieve_state
def update(state: dict, azure_token: str, identity_id: str, email: str, role: str) -> CommandResponse:
    """
    Update the specified access to User for a Solution
    """
    service_state = state["services"]
    service = SolutionSecurityService(azure_token=azure_token, state=service_state)
    details = json.dumps({"id": email, "role": role})
    response = service.update_control_access(identity_id, details)
    return CommandResponse.success(response, verbose=True)
