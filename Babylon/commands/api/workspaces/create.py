import pathlib

from logging import getLogger
from typing import Any
from click import argument, command
from click import option
from click import Path
from Babylon.commands.api.workspaces.service.api import WorkspaceService
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
)
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_azure_token

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", type=str)
@argument("payload_file", type=Path(path_type=pathlib.Path))
@retrieve_state
def create(
    state: Any,
    azure_token: str,
    organization_id: str,
    payload_file: pathlib.Path = None,
) -> CommandResponse:
    """
    Register a workspace.
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])

    spec = dict()
    if not payload_file.exists():
        print(f"file {payload_file} not found in directory")
        return CommandResponse.fail()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template(f.read(), state)
    workspace_service = WorkspaceService(state=service_state, azure_token=azure_token, spec=spec)
    response = workspace_service.create()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    state["services"]["api"]["workspace_id"] = workspace.get("id")
    state["services"]["api"]["workspace_key"] = workspace.get("key")
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    logger.info(f"Workspace {workspace['id']} successfully saved in state {state.get('id')}")
    return CommandResponse.success(workspace, verbose=True)
