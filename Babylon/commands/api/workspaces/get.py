from logging import getLogger
from typing import Any
from click import command, option

from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", type=str)
@option("--workspace-id", type=str)
@retrieve_state
def get(state: Any, organization_id: str, azure_token: str, workspace_id: str) -> CommandResponse:
    """
    Get a workspace details
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    workspace_service = WorkspaceService(state=service_state, azure_token=azure_token)
    response = workspace_service.get()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    return CommandResponse.success(workspace, verbose=True)
