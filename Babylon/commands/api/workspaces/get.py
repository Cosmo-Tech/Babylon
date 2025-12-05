from logging import getLogger
from typing import Any

from click import argument, command, echo, style

from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
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
@retrieve_state
def get(state: Any, config: Any, organization_id: str, keycloak_token: str, workspace_id: str) -> CommandResponse:
    """
    Get a workspace details

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
    """
    _work = [""]
    _work.append("Get a workspace details")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    workspace_service = WorkspaceService(state=services_state, keycloak_token=keycloak_token, config=config)
    logger.info(f"Retrieving workspace {[services_state['workspace_id']]} details")
    response = workspace_service.get()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    return CommandResponse.success(workspace)
