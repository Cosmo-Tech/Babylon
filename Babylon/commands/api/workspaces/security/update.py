import json
import logging

from click import argument, command, option
from Babylon.commands.api.workspaces.security.service.api import (
    ApiWorkspaceSecurityService, )
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file, retrieve_state, timing_decorator

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_azure_token("csm_api")
@output_to_file
@option(
    "--role",
    "role",
    type=str,
    required=True,
    default="viewer",
    help="Role RBAC",
)
@option("--email", "email", type=str, required=True, help="Email valid")
@argument("id", type=str)
@retrieve_state
def update(state: dict, azure_token: str, id: str, email: str, role: str) -> CommandResponse:
    """
    Update workspace users RBAC access
    """
    service_state = state["services"]
    details = json.dumps({"id": email, "role": role})
    service = ApiWorkspaceSecurityService(azure_token=azure_token, state=service_state)
    response = service.update(id=id, details=details)
    return CommandResponse.success(response, verbose=True)
