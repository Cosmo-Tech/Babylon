import json
import logging

from click import command, echo, option, style

from Babylon.commands.api.workspaces.services.workspaces_security_svc import (
    ApiWorkspaceSecurityService,
)
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger(__name__)
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
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@retrieve_state
def update(
    state: dict, organization_id: str, workspace_id: str, keycloak_token: str, email: str, role: str
) -> CommandResponse:
    """
    Update workspace users RBAC access
    """
    _work = [""]
    _work.append("Update workspace users RBAC access")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or service_state["api"]["workspace_id"]
    details = json.dumps({"id": email, "role": role})
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Updating user {[email]} RBAC access in the workspace {[service_state['api']['workspace_id']]}")
    response = service.update(id=email, details=details)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(json.dumps(rbacs, indent=2))
    logger.info(f"User {[email]} RBAC access successfully Updated")
    return CommandResponse.success(rbacs)
