from logging import getLogger
from typing import Any
from click import command, option, echo, style
from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@retrieve_state
def get(state: Any, organization_id: str, keycloak_token: str, workspace_id: str) -> CommandResponse:
    """
    Get a workspace details
    """
    _work = [""]
    _work.append("Get a workspace details")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    workspace_service = WorkspaceService(state=service_state, keycloak_token=keycloak_token)
    logger.info(f"Retrieving workspace {[service_state['api']['workspace_id']]} details")
    response = workspace_service.get()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    return CommandResponse.success(workspace)
