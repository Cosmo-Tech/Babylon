from logging import getLogger
from typing import Any, Optional

import jmespath
from click import argument, command, echo, option, style

from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config_state
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
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_config_state
def get_all(
    state: Any, config: Any, organization_id: str, workspace_id: str, keycloak_token: str, filter: Optional[str] = None
) -> CommandResponse:
    """
    Get all workspaces details

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
    """
    _work = [""]
    _work.append("Get all workspaces details")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    workspace_service = WorkspaceService(state=services_state, keycloak_token=keycloak_token, config=config)
    logger.info(f"Getting all workspaces from organization {[services_state['organization_id']]}")
    response = workspace_service.get_all()
    if response is None:
        return CommandResponse.fail()
    workspaces = response.json()
    if len(workspaces) and filter:
        workspaces = jmespath.search(filter, workspaces)
    logger.info(f"Retrieved workspaces {[w.get('id') for w in workspaces]}")
    return CommandResponse.success(workspaces)
