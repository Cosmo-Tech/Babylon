import pathlib
import click
from logging import getLogger
from typing import Any
from click import argument, command
from click import option
from click import Path
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
@option("--organization-id", type=str)
@argument("payload_file", type=Path(path_type=pathlib.Path))
@retrieve_state
def create(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    payload_file: pathlib.Path = None,
) -> CommandResponse:
    """
    Register a workspace.
    """
    _ret = [""]
    _ret.append("Register a workspace")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])

    spec = dict()
    if not payload_file.exists():
        print(f"file {payload_file} not found in directory")
        return CommandResponse.fail()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    workspace_service = WorkspaceService(state=service_state, keycloak_token=keycloak_token, spec=spec)
    response = workspace_service.create()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    state["services"]["api"]["workspace_id"] = workspace.get("id")
    state["services"]["api"]["workspace_key"] = workspace.get("key")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    logger.info(f"Workspace {workspace['id']} successfully saved in state {state.get('id')}")
    return CommandResponse.success(workspace, verbose=True)
