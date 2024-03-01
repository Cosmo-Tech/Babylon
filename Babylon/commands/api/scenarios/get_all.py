from logging import getLogger

import jmespath
from click import command, option
from typing import Any, Optional

from Babylon.commands.api.scenarios.services.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    timing_decorator,
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
@pass_azure_token("csm_api")
@timing_decorator
@output_to_file
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(
    state: Any,
    organization_id: str,
    workspace_id: str,
    azure_token: str,
    filter: Optional[str],
) -> CommandResponse:
    """
    Get all scenarios in the workspace
    """

    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or service_state["api"]["workspace_id"])

    logger.info(f"Getting all scenarios from workspace {service_state['api']['workspace_id']}")

    scenario_service = ScenarioService(state=service_state, azure_token=azure_token)
    response = scenario_service.get_all()
    if response is None:
        return CommandResponse.fail()
    scenarios = response.json()
    if len(scenarios) and filter:
        scenarios = jmespath.search(filter, scenarios)
    return CommandResponse.success(scenarios, verbose=True)
