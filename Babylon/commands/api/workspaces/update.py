import pathlib
import json

from logging import getLogger
from typing import Any
from click import command, argument, option, echo, style, Path
from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
)
from Babylon.utils.decorators import output_to_file
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@retrieve_state
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
def update(
    state: Any,
    organization_id: str,
    keycloak_token: str,
    workspace_id: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Update a workspace
    """
    _work = [""]
    _work.append("Update a workspace")
    _work.append("")
    echo(style("\n".join(_work), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    workspace_service = WorkspaceService(state=service_state, keycloak_token=keycloak_token, spec=spec)
    logger.info(f"[api] Updating workspace {[service_state['api']['workspace_id']]}")
    response = workspace_service.update()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    logger.info(json.dumps(workspace, indent=2))
    logger.info(f"[api] Workspace {[service_state['api']['workspace_id']]} successfully updated")
    return CommandResponse.success(workspace)
