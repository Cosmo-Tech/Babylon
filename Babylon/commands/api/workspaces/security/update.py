import logging
from json import dumps

from click import argument, command, echo, option, style

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
@option("--role", "role", type=str, required=True, help="Role RBAC")
@option("--email", "email", type=str, required=True, help="Email valid")
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@retrieve_state
def update(
    state: dict, config: dict, organization_id: str, workspace_id: str, keycloak_token: str, email: str, role: str
) -> CommandResponse:
    """
    Update workspace users RBAC access

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
    """
    _work = [""]
    _work.append("Update workspace users RBAC access")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    details = dumps({"id": email, "role": role})
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Updating user {[email]} RBAC access in the workspace {[services_state['workspace_id']]}")
    response = service.update(id=email, details=details)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(dumps(rbacs, indent=2))
    logger.info(f"User {[email]} RBAC access successfully Updated")
    return CommandResponse.success(rbacs)
