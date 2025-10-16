from logging import getLogger
from typing import Any
from click import command, option, echo, style
from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@retrieve_state
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--runner-id", "runner_id", type=str)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
def delete(
    state: Any,
    organization_id: str,
    workspace_id: str,
    keycloak_token: str,
    runner_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a runner
    """
    _run = [""]
    _run.append("Delete a runner")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    service_state["api"]["runner_id"] = (runner_id or state["services"]["api"]["runner_id"])
    runner_service = RunnerService(state=service_state, keycloak_token=keycloak_token)
    logger.info("[api] Deleting runner")
    response = runner_service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f'[api] Runner {[service_state["api"]["runner_id"]]} successfully deleted')
    state["services"]["api"]["runner_id"] = ""
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    return CommandResponse.success(response)
