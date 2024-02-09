import pathlib

from logging import getLogger
from typing import Any, Optional
from click import command
from click import option
from click import Path

from Babylon.commands.api.workspaces.service.api import WorkspaceService

from Babylon.utils.checkers import check_ascii, check_email
from Babylon.utils.decorators import (
    wrapcontext,
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
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@retrieve_state
@option(
    "--payload",
    "payload",
    type=Path(path_type=pathlib.Path),
    help="Your custom workspace description file (yaml or json)",
)
@option("--email", "security_id", help="Workspace security_id aka email")
@option(
    "--role",
    "security_role",
    required=True,
    default="admin",
    help="Workspace security role",
)
@option("--organization-id", type=str)
@option("--name", "name", type=str)
def create(
    state: Any,
    azure_token: str,
    organization_id: str,
    name: Optional[str],
    payload: Optional[pathlib.Path] = None,
    security_id: Optional[str] = None,
    security_role: Optional[str] = None,
) -> CommandResponse:
    """
    Register a workspace.
    """

    data = dict()
    if name:
        check_ascii(name)
        data["name"] = name
    if security_id:
        check_email(security_id)
        data["security_id"] = security_id
    if security_role:
        data["security_role"] = security_role

    details = env.fill_template(payload, data)

    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])

    workspace_service = WorkspaceService(state=service_state, azure_token=azure_token, spec=details)
    response = workspace_service.create()
    if response is None:
        return CommandResponse.fail()
    workspace = response.json()
    if organization_id:
        state["services"]["api"]["organization_id"] = organization_id
        env.store_state_in_local(state)
        env.store_state_in_cloud(state)
    state["services"]["api"]["workspace_id"] = workspace["id"]
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    logger.info(f"Workspace {workspace['id']} successfully saved in state")
    return CommandResponse.success(workspace, verbose=True)
