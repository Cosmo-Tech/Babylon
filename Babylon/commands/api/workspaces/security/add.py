import json

from logging import getLogger
from typing import Any
from click import option
from click import command
from Babylon.commands.api.workspaces.services.workspaces_security_svc import ApiWorkspaceSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--role", "role", type=str, required=True, default="viewer", help="Role RBAC")
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def add(
    state: Any,
    keycloak_token: str,
    role: str,
    email: str,
) -> CommandResponse:
    """
    Add workspace users RBAC access
    """
    service_state = state["services"]
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=service_state)
    details = json.dumps(obj={"id": email, "role": role}, indent=2, ensure_ascii=True)
    response = service.add(details)
    logger.info(json.dumps(response.json(), indent=2))
    return CommandResponse.success(response, verbose=True)
