import json
from logging import getLogger
from typing import Any

from click import command, echo, option, style

from Babylon.commands.api.workspaces.services.workspaces_security_svc import ApiWorkspaceSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    output_to_file,
    retrieve_state,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@retrieve_state
def set_default(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    role: str = None,
) -> CommandResponse:
    """
    Set default RBAC access to workspace
    """
    _work = [""]
    _work.append("Set default RBAC access to workspace")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or service_state["api"]["workspace_id"]
    service = ApiWorkspaceSecurityService(keycloak_token=keycloak_token, state=service_state)
    details = json.dumps(obj={"role": role}, indent=2, ensure_ascii=True)
    logger.info(f"Setting default RBAC access to the solution {[service_state['api']['workspace_id']]}")
    response = service.set_default(details)
    if response is None:
        return CommandResponse.fail()
    default_security = response.json()
    logger.info(json.dumps(default_security, indent=2))
    logger.info(f"default RBAC access successfully set with role {[role]}")
    return CommandResponse.success(default_security)
