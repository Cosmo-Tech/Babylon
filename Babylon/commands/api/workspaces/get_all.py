import jmespath
from logging import getLogger
from typing import Any, Optional
from click import command
from click import option

from Babylon.commands.api.workspaces.service.api import WorkspaceService
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
)
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", type=str)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, organization_id: str, azure_token: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all workspaces details
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    workspace_service = WorkspaceService(state=service_state, azure_token=azure_token)
    response = workspace_service.get_all()
    if response is None:
        return CommandResponse.fail()
    workspaces = response.json()
    if len(workspaces) and filter:
        workspaces = jmespath.search(filter, workspaces)
    return CommandResponse.success(workspaces, verbose=True)
