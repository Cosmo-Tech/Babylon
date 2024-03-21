import json

from logging import getLogger
from typing import Any
from click import option
from click import command
from Babylon.commands.api.workspaces.services.workspaces_security_svc import ApiWorkspaceSecurityService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


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
    Add workspace users RBAC access
    """
    service_state = state["services"]
    service = ApiWorkspaceSecurityService(azure_token=azure_token, state=service_state)
    details = json.dumps(obj={"id": email, "role": role}, indent=2, ensure_ascii=True)
    response = service.add(details)
    return CommandResponse.success(response, verbose=True)
