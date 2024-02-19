from logging import getLogger
from typing import Any
from click import command
from click import option

from Babylon.commands.api.workspaces.service.api import WorkspaceService
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
)
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@retrieve_state
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, default=True, help="Force Delete")
@option("--organization-id", type=str)
@option("--workspace-id", type=str)
def delete(
    state: Any,
    azure_token: str,
    organization_id: str,
    workspace_id: str,
    force_validation: bool = True,
) -> CommandResponse:
    """
    Delete a workspace
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    if not force_validation and not confirm_deletion("workspace", workspace_id):
        return CommandResponse.fail()
    workspace_service = WorkspaceService(state=service_state, azure_token=azure_token)
    response = workspace_service.delete()
    if response is None:
        return CommandResponse.fail()
    if response:
        logger.info(f'Workspace {service_state["api"]["workspace_id"]} successfully deleted')
        if (service_state["api"]["workspace_id"] == state["services"]["api"]["workspace_id"]):
            state["services"]["api"]["workspace_id"] = ""
            env.store_state_in_local(state)
            env.store_state_in_cloud(state)
            logger.info(
                f'Workspace {service_state["api"]["workspace_id"]} successfully deleted in state {state.get("id")}')
    return CommandResponse.success()
