import jmespath
import json

from logging import getLogger
from typing import Any, Optional
from click import command, option, echo, style
from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
)
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any,
            organization_id: str,
            workspace_id: str,
            keycloak_token: str,
            filter: Optional[str] = None) -> CommandResponse:
    """
    Get all workspaces details
    """
    _work = [""]
    _work.append("Get all workspaces details")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])
    workspace_service = WorkspaceService(state=service_state, keycloak_token=keycloak_token)
    logger.info(f"[api] Getting all workspaces from organization {[service_state['api']['organization_id']]}")
    response = workspace_service.get_all()
    if response is None:
        return CommandResponse.fail()
    workspaces = response.json()
    if len(workspaces) and filter:
        workspaces = jmespath.search(filter, workspaces)
    logger.info(json.dumps(workspaces, indent=2))
    return CommandResponse.success(workspaces)
