import json
import logging

from click import argument, command, option
from Babylon.commands.api.workspaces.services.workspaces_security_svc import (
    ApiWorkspaceSecurityService, )
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file, retrieve_state

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
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
def update(state: dict, keycloak_token: str, id: str, email: str, role: str) -> CommandResponse:
    """
    Update workspace users RBAC access
    """
    service_state = state["services"]
    details = json.dumps({"id": email, "role": role})
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=service_state)
    response = service.update(id=id, details=details)
    logger.info(json.dumps(response.json(), indent=2))
    return CommandResponse.success(response, verbose=True)
