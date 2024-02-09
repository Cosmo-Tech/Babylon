import pathlib

from logging import getLogger
from typing import Any
from click import Path
from click import command
from click import option

from Babylon.commands.api.workspaces.service.api import WorkspaceService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    wrapcontext,
    retrieve_state,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()

payload = {"name": "Updated workspace to be deleted"}


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@retrieve_state
@option(
    "--organization-id",
    "organization_id",
    type=str,
    help="Organization Id Cosmotech Platform",
)
@option(
    "--payload",
    "payload",
    type=Path(path_type=pathlib.Path),
    help="Your custom workspace description file yaml",
)
@option("--workspace-id", "workspace_id", type=str)
def update(
    state: Any,
    organization_id: str,
    workspace_id: str,
    payload: pathlib.Path,
    azure_token: str,
) -> CommandResponse:
    """
    Update a workspace
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])

    details = env.fill_template(payload)

    workspace_service = WorkspaceService(state=service_state, azure_token=azure_token, spec=details)
    response = workspace_service.update()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    if workspace_id:
        state["services"]["api"]["workspace_id"] = workspace["id"]
        env.store_state_in_local(state)
        env.store_state_in_cloud(state)
        logger.info(f"Scenario {workspace_id} has been successfully added in state")
    return CommandResponse.success(workspace, verbose=True)
