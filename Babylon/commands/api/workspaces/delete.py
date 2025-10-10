import click
from logging import getLogger
from typing import Any
from click import command
from click import option

from Babylon.commands.api.workspaces.services.workspaces_api_svc import WorkspaceService
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_keycloak_token

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@retrieve_state
@pass_keycloak_token()
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@option("--organization-id", type=str)
@option("--workspace-id", type=str)
def delete(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    force_validation: bool,
) -> CommandResponse:
    """
    Delete a workspace
    """
    _ret = [""]
    _ret.append("Delete a workspace")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    workspace_service = WorkspaceService(state=service_state, keycloak_token=keycloak_token)
    logger.info("[api] Deleting workspace")
    response = workspace_service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"[api] Workspace {[service_state['api']['workspace_id']]} successfully deleted")
    state["services"]["api"]["workspace_id"] = ""
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    return CommandResponse.success()
