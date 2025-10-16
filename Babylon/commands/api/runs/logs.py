from logging import getLogger
from typing import Any
from click import command, option, echo, style
from Babylon.commands.api.runs.services.run_api_svc import RunService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--run-id", "run_id", type=str)
@option("--runner-id", "runner_id", type=str)
@retrieve_state
def logs(state: Any, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str,
         run_id: str) -> CommandResponse:
    """
    Get the logs for the Run
    """
    _run = [""]
    _run.append("Get the logs for the Run")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    service_state = state['services']
    service_state['api']['organization_id'] = organization_id or service_state['api']['organization_id']
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    service_state["api"]["runner_id"] = (runner_id or state["services"]["api"]["runner_id"])
    service_state['api']['run_id'] = run_id or service_state['api'].get('run_id')
    service = RunService(state=service_state, keycloak_token=keycloak_token)
    logger.info(f"[api] Getting logs for run {[service_state['api']['run_id']]}")
    response = service.logs()
    if response is None:
        return CommandResponse.fail()
    run_logs = response.json()
    return CommandResponse.success(run_logs, verbose=True)
