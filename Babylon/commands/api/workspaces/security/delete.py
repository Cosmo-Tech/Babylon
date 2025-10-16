import logging

from click import option, command, echo, style
from Babylon.commands.api.workspaces.services.workspaces_security_svc import ApiWorkspaceSecurityService
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
@option("--email", "email", type=str, required=True, help="Email valid")
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@retrieve_state
def delete(state: dict, organization_id: str, workspace_id: str, keycloak_token: str, email: str) -> CommandResponse:
    """
    Delete workspace users RBAC access
    """
    _work = [""]
    _work.append("Delete workspace users RBAC access")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Deleting user {[email]} RBAC permissions on workspace {[service_state['api']['workspace_id']]}")
    response = service.delete(id=email)
    if response is None:
        return CommandResponse.fail()
    logger.info("[api] User RBAC permissions successfully deleted")
    return CommandResponse.success(response)
