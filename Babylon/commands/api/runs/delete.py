from logging import getLogger
from typing import Any

from click import command, echo, option, style

from Babylon.commands.api.runs.services.run_api_svc import RunService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--run-id", "run_id", type=str)
@option("--runner-id", "runner_id", type=str)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@retrieve_state
def delete(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    workspace_id: str,
    runner_id: str,
    run_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete the run
    """
    _run = [""]
    _run.append("Delete the Run")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or state["services"]["api"]["workspace_id"]
    service_state["api"]["runner_id"] = runner_id or state["services"]["api"]["runner_id"]
    service_state["api"]["run_id"] = run_id or service_state["api"].get("run_id")
    service = RunService(state=service_state, keycloak_token=keycloak_token)
    logger.info(f"Deleting run {[service_state['api']['run_id']]}")
    response = service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Run {[service_state['api']['run_id']]} successfully deleted")
    state["services"]["api"]["run_id"] = ""
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    return CommandResponse.success(response)
