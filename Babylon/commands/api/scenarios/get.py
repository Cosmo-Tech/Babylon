from logging import getLogger
from typing import Any

from click import command, option

from Babylon.commands.api.scenarios.services.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import (
    timing_decorator,
    injectcontext,
    retrieve_state,
    output_to_file,
)
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@injectcontext()
@pass_azure_token("csm_api")
@timing_decorator
@output_to_file
@retrieve_state
@option("--organization-id", "organization_id", type=str)
@option("--workspace-id", "workspace_id", type=str)
@option("--scenario-id", type=str)
def get(
    state: Any,
    organization_id: str,
    workspace_id: str,
    scenario_id: str,
    azure_token: str,
) -> CommandResponse:
    """
    Get scenario details
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    service_state["api"]["scenario_id"] = (scenario_id or state["services"]["api"]["scenario_id"])

    scenario_service = ScenarioService(state=service_state, azure_token=azure_token)
    response = scenario_service.get()
    if response is None:
        return CommandResponse.fail()
    scenario = response.json()
    return CommandResponse.success(scenario, verbose=True)
