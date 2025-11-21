from logging import getLogger
from typing import Any, Optional

import jmespath
from click import command, echo, option, style

from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    output_to_file,
    retrieve_state,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

env = Environment()
logger = getLogger(__name__)


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(
    state: Any,
    organization_id: str,
    workspace_id: str,
    keycloak_token: str,
    filter: Optional[str],
) -> CommandResponse:
    """
    Get all runners in the workspace
    """
    _run = [""]
    _run.append("Get all runners details")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["workspace_id"] = workspace_id or service_state["api"]["workspace_id"]
    runner_service = RunnerService(state=service_state, keycloak_token=keycloak_token)
    logger.info(f"Getting all runners from workspace {[service_state['api']['workspace_id']]}")
    response = runner_service.get_all()
    if response is None:
        return CommandResponse.fail()
    runners = response.json()
    if len(runners) and filter:
        runners = jmespath.search(filter, runners)
    logger.info(f"Retrieved runners: {[r.get('id') for r in runners]}")
    return CommandResponse.success(runners)
