import pathlib
import json

from logging import getLogger
from typing import Any
from click import argument, command, option, echo, style, Path
from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
)
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_keycloak_token

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_state
def create(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    payload_file: pathlib.Path = None,
) -> CommandResponse:
    """
    Register a workspace.
    """
    _work = [""]
    _work.append("Register a workspace")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["workspace_id"] = organization_id or service_state["api"]["workspace_id"]
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    workspace_service = WorkspaceService(state=service_state, keycloak_token=keycloak_token, spec=spec)
    logger.info("[api] Creating workspace")
    response = workspace_service.create()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    state["services"]["api"]["workspace_id"] = workspace.get("id")
    state["services"]["api"]["workspace_key"] = workspace.get("key")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    logger.info(json.dumps(workspace, indent=2))
    logger.info(f"[api] Workspace {[workspace.get('id')]} successfully created")
    return CommandResponse.success(workspace)
