import json
from logging import getLogger
from typing import Any
from click import command
from click import option
from Babylon.commands.api.workspaces.services.workspaces_security_svc import ApiWorkspaceSecurityService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
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
    azure_token: str,
    organization_id: str,
    workspace_id: str,
    role: str = None,
) -> CommandResponse:
    """
    Set default RBAC access to workspace
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or state["services"]["api"]["workspace_id"]
    service = ApiWorkspaceSecurityService(azure_token=azure_token, state=service_state)
    details = json.dumps(obj={"role": role}, indent=2, ensure_ascii=True)
    response = service.set_default(details)
    default_security = response.json()
    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(default_security, verbose=True)
