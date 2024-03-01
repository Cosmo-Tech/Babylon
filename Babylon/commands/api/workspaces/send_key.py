from logging import getLogger
from typing import Any
from click import command, option
from Babylon.commands.api.workspaces.service.api import WorkspaceService
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@retrieve_state
def send_key(
    state: Any,
    azure_token: str,
    organization_id: str,
    workspace_id: str,
) -> CommandResponse:
    """
    Send Event Hub key to given workspace
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])
    workspace_service = WorkspaceService(state=service_state, azure_token=azure_token)
    response = workspace_service.send_key()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()    
    logger.info(f'Successfully update key in workspace {service_state["api"]["workspace_id"]}')
    return CommandResponse.success(workspace, verbose=True)
