from logging import getLogger
from typing import Any

from click import argument, command, echo, style

from Babylon.commands.api.runs.services.run_api_svc import RunService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("runner_id", required=True)
@argument("run_id", required=True)
@retrieve_state
def logs(
    state: Any, config: Any, keycloak_token: str, organization_id: str, workspace_id: str, runner_id: str, run_id: str
) -> CommandResponse:
    """
    Get the logs for the Run

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       RUNNER_ID : The unique identifier of the runner
       RUN_ID: The unique identifier of the run
    """
    _run = [""]
    _run.append("Get the logs for the Run")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    services_state["runner_id"] = runner_id or services_state["runner_id"]
    services_state["run_id"] = run_id or services_state.get("run_id")
    service = RunService(state=services_state, keycloak_token=keycloak_token, config=config)
    logger.info(f"Getting logs for run {[services_state['run_id']]}")
    response = service.logs()
    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(response.text)
