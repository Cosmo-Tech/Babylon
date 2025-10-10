from logging import getLogger

from click import command, option
from typing import Any, Optional

from Babylon.commands.api.runners.services.runner_api_svc import RunnerService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import (
    injectcontext,
    retrieve_state,
    output_to_file,
)
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

env = Environment()
logger = getLogger("Babylon")


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

    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])

    logger.info(f"Getting all runners from workspace {service_state['api']['workspace_id']}")

    runner_service = RunnerService(state=service_state, keycloak_token=keycloak_token)
    response = runner_service.get_all()
    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(response.json(), verbose=True)
