from json import dumps
from logging import getLogger
from typing import Any

from click import argument, command, echo, style

from Babylon.commands.api.workspaces.services.workspaces_security_svc import ApiWorkspaceSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    output_to_file,
    retrieve_config_state,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@retrieve_config_state
def get_all(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
) -> CommandResponse:
    """
    Get all RBAC access for the workspace
    """
    _work = [""]
    _work.append("Get all RBAC access for the workspace")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"[api] Retrieving all RBAC access to the workspace {[services_state['workspace_id']]}")
    response = service.get_all()
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(dumps(rbacs, indent=2))
    return CommandResponse.success(rbacs)
