from logging import getLogger
from typing import Any
from click import command, option
from Babylon.commands.api.workspaces.services.api import WorkspaceService
from Babylon.utils.decorators import (
    retrieve_state,
    injectcontext,
)
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--workspace-key", "workspace_key", type=str)
@retrieve_state
def send_key(
    state: Any,
    azure_token: str,
    organization_id: str,
    workspace_id: str,
    workspace_key: str,
) -> CommandResponse:
    """
    Send Event Hub key to given workspace
    """
    state["services"]["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    state["services"]["api"]["workspace_id"] = workspace_id or state["services"]["api"]["workspace_id"]
    state["services"]["api"]["workspace_key"] = workspace_key or state["services"]["api"]["workspace_key"]
    service_state = state['services']
    workspace_service = WorkspaceService(state=service_state, azure_token=azure_token)
    response = workspace_service.send_key(workspace_id=workspace_id, workspace_key=workspace_key)
    if response is None:
        return CommandResponse.fail()
    logger.info(f'[api] successfully updated key in workspace {service_state["api"]["workspace_id"]}')
    return CommandResponse.success()
