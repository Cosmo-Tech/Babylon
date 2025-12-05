from json import dumps
from logging import getLogger
from typing import Any

from click import argument, command, echo, option, style

from Babylon.commands.api.workspaces.services.workspaces_security_svc import ApiWorkspaceSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--role", "role", type=str, required=True, default="viewer", help="Role RBAC")
@option("--email", "email", type=str, required=True, help="Email valid")
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@retrieve_state
def add(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    role: str,
    email: str,
) -> CommandResponse:
    """
    Add workspace users RBAC access

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
    """
    _work = [""]
    _work.append("Add workspace users RBAC access")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    details = dumps(obj={"id": email, "role": role}, indent=2, ensure_ascii=True)
    logger.info(f"Granting user {[email]} RBAC permissions on workspace {[services_state['workspace_id']]}")
    response = service.add(details)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(dumps(rbacs, indent=2))
    logger.info("User RBAC permissions successfully added")
    return CommandResponse.success(rbacs)
