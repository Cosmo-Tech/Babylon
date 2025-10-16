import json

from logging import getLogger
from typing import Any
from click import command, option, echo, style
from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
    output_to_file,
)
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@retrieve_state
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--runner-id", "runner_id", type=str)
def get(
    state: Any,
    organization_id: str,
    workspace_id: str,
    runner_id: str,
    keycloak_token: str,
) -> CommandResponse:
    """
    Get runner details
    """
    _run = [""]
    _run.append("Get runner details")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    service_state["api"]["runner_id"] = (runner_id or state["services"]["api"]["runner_id"])
    runner_service = RunnerService(state=service_state, keycloak_token=keycloak_token)
    logger.info(f"[api] Retrieving runner {[service_state['api']['runner_id']]} details")
    response = runner_service.get()
    if response is None:
        return CommandResponse.fail()
    runner = response.json()
    logger.info(json.dumps(runner, indent=2))
    return CommandResponse.success(runner)
