import click
from logging import getLogger
from typing import Any
from click import option, command, argument
from Babylon.commands.api.workspaces.services.workspaces_security_svc import (
    ApiWorkspaceSecurityService,
)
from Babylon.utils.credentials import pass_keycloak_token
from json import dumps
from Babylon.utils.decorators import retrieve_config_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--email", "email", type=str, required=True, help="Email valid")
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@retrieve_config_state
def get(state: Any, config: Any, organization_id: str, workspace_id: str, keycloak_token: str,
        email: str) -> CommandResponse:
    """
    Get workspace users RBAC access

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
    """
    _work = [""]
    _work.append("Get workspace users RBAC access")
    _work.append("")
    click.echo(click.style("\n".join(_work), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Get user {[email]} RBAC access to the workspace {[services_state['workspace_id']]}")
    response = service.get(id=email)
    if response is None:
        return CommandResponse.fail()
    logger.info(dumps(response.json(), indent=2))
    return CommandResponse.success(response)
