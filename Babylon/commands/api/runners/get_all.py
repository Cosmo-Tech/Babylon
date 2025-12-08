from logging import getLogger
from typing import Any, Optional

import jmespath
from click import argument, command, echo, option, style

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
@argument("organization_id", required=True)
@argument("workspace_id", required=True)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(
    state: Any,
    config: Any,
    organization_id: str,
    workspace_id: str,
    keycloak_token: str,
    filter: Optional[str],
) -> CommandResponse:
    """
    Get all runners in the workspace

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       WORKSPACE_ID : The unique identifier of the workspace
    """
    _run = [""]
    _run.append("Get all runners details")
    _run.append("")
    echo(style("\n".join(_run), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["workspace_id"] = workspace_id or services_state["workspace_id"]
    runner_service = RunnerService(state=services_state, keycloak_token=keycloak_token, config=config)
    logger.info(f"Getting all runners from workspace {[services_state['workspace_id']]}")
    response = runner_service.get_all()
    if response is None:
        return CommandResponse.fail()
    runners = response.json()
    if len(runners) and filter:
        runners = jmespath.search(filter, runners)
    logger.info(f"Retrieved runners: {[r.get('id') for r in runners]}")
    return CommandResponse.success(runners)
