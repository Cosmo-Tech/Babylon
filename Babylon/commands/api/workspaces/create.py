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
@argument("organization_id", required=True)
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_config_state
def create(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    payload_file: pathlib.Path = None,
) -> CommandResponse:
    """
    Register a specific workspace

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       PAYLOAD_FILE : Path to the manifest file used to update the workspace
    """
    _work = [""]
    _work.append("Register a workspace")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    spec = dict()
    with open(payload_file, "r") as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    workspace_service = WorkspaceService(state=services_state, keycloak_token=keycloak_token, spec=spec, config=config)
    logger.info("Creating workspace")
    response = workspace_service.create()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    state["services"]["api"]["workspace_id"] = workspace.get("id")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    logger.info(f"Workspace {[workspace.get('id')]} successfully created")
    return CommandResponse.success(workspace)
