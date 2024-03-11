import json
from typing import Any
from click import option
from click import command
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.commands.api.solutions.services.security import SolutionSecurityService


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--role", "role", type=str, required=True, default="viewer", help="Role RBAC")
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def add(
    state: Any,
    azure_token: str,
    role: str,
    email: str,
) -> CommandResponse:
    """
    Add a control access to the Solution
    """
    service_state = state["services"]
    service = SolutionSecurityService(azure_token=azure_token, state=service_state)
    details = json.dumps(obj={"id": email, "role": role}, indent=2, ensure_ascii=True)
    response = service.add_control_access(details)
    return CommandResponse.success(response, verbose=True)
