import pathlib

from logging import getLogger
from typing import Any
from click import Path, argument
from click import command
from click import option
from Babylon.commands.api.workspaces.services.api import WorkspaceService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    injectcontext,
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
@injectcontext()
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
@argument("payload_file", type=Path(path_type=pathlib.Path))
@option("--workspace-id", "workspace_id", type=str)
def update(
    state: Any,
    organization_id: str,
    azure_token: str,
    workspace_id: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Update a workspace
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    if not payload_file.exists():
        print(f"file {payload_file} not found in directory")
        return CommandResponse.fail()
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template(f.read(), state)
    workspace_service = WorkspaceService(state=service_state, azure_token=azure_token, spec=spec)
    response = workspace_service.update()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    if response:
        logger.info(f'Workspace {service_state["api"]["workspace_id"]} successfully updated')
        if (service_state["api"]["workspace_id"] == state["services"]["api"]["workspace_id"]):
            logger.info(
                f'Workspace {state["services"]["api"]["workspace_id"]} stored in state has been successfully updated')
    return CommandResponse.success(workspace, verbose=True)
