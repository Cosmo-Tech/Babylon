import logging

from click import option, command, echo, style, argument
from Babylon.commands.api.workspaces.services.workspaces_security_svc import ApiWorkspaceSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file, retrieve_config_state

logger = logging.getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@option("--email", "email", type=str, required=True, help="Email valid")
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@retrieve_config_state
def delete(state: dict, config: dict, organization_id: str, workspace_id: str, keycloak_token: str, email: str) -> CommandResponse:
    """
    Delete workspace users RBAC access

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
    """
    _work = [""]
    _work.append("Delete workspace users RBAC access")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = (organization_id or services_state["organization_id"])
    services_state["workspace_id"] = (workspace_id or services_state["workspace_id"])
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Deleting user {[email]} RBAC permissions on workspace {[services_state['workspace_id']]}")
    response = service.delete(id=email)
    if response is None:
        return CommandResponse.fail()
    logger.info("User RBAC permissions successfully deleted")
    return CommandResponse.success(response)
