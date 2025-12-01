from logging import getLogger
from typing import Any

from click import argument, command, echo, style

from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    output_to_file,
    retrieve_config_state,
)
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@retrieve_config_state
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@argument("runner_id", required=True)
def get(
    state: Any,
    config: Any,
    organization_id: str,
    workspace_id: str,
    runner_id: str,
    keycloak_token: str,
) -> CommandResponse:
    """
    Get runner details

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
       RUNNER_ID : The unique identifier of the runner
    """
    _run = [""]
    _run.append("Get runner details")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    services_state["runner_id"] = runner_id or services_state["runner_id"]
    runner_service = RunnerService(state=services_state, keycloak_token=keycloak_token, config=config)
    logger.info(f"Retrieving runner {[services_state['runner_id']]} details")
    response = runner_service.get()
    if response is None:
        return CommandResponse.fail()
    runner = response.json()
    return CommandResponse.success(runner)
