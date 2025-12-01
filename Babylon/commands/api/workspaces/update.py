import pathlib
from logging import getLogger
from typing import Any

from click import Path, argument, command, echo, style

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
@retrieve_config_state
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
def update(
    state: Any,
    config: Any,
    organization_id: str,
    keycloak_token: str,
    workspace_id: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Update a specific workspace

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       PAYLOAD_FILE : Path to the manifest file used to update the workspace
    """
    _work = [""]
    _work.append("Update a workspace")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    spec = dict()
    with open(payload_file, "r") as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    workspace_service = WorkspaceService(state=services_state, keycloak_token=keycloak_token, spec=spec, config=config)
    logger.info(f"Updating workspace {[services_state['workspace_id']]}")
    response = workspace_service.update()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    logger.info(f"Workspace {[services_state['workspace_id']]} successfully updated")
    return CommandResponse.success(workspace)
