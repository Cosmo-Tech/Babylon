from logging import getLogger
from typing import Any

from click import command, echo, option, style

from Babylon.commands.api.runs.services.run_api_svc import RunService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    output_to_file,
    retrieve_state,
)
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@retrieve_state
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--run-id", "run_id", type=str)
@option("--runner-id", "runner_id", type=str)
def get_all(
    state: Any,
    organization_id: str,
    workspace_id: str,
    run_id: str,
    runner_id: str,
    keycloak_token: str,
) -> CommandResponse:
    """
    Get run details
    """
    _run = [""]
    _run.append("Get run details")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or state["services"]["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or state["services"]["api"]["workspace_id"]
    service_state["api"]["runner_id"] = runner_id or state["services"]["api"]["runner_id"]
    service_state["api"]["run_id"] = run_id or state["services"]["api"]["run_id"]
    run_service = RunService(state=service_state, keycloak_token=keycloak_token)
    logger.info(f"Retrieving all runs from runner {[service_state['api']['runner_id']]}")
    response = run_service.get_all()
    if response is None:
        return CommandResponse.fail()
    runs = response.json()
    logger.info(f"Retrieved runs {[r.get('id') for r in runs]}")
    return CommandResponse.success(runs)
