from logging import getLogger
from typing import Any

from click import command, option

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_azure_token("csm_api")
@timing_decorator
@retrieve_state
@option("--organization-id", "organization_id", type=str, required=False)
@option("--workspace-id", "workspace_id", type=str, required=False)
@option("--scenario-id", type=str, required=False)
def delete(
    state: Any,
    organization_id: str,
    workspace_id: str,
    azure_token: str,
    scenario_id: str,
) -> CommandResponse:
    """
    Delete a scenario
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or state["services"]["api"]["organization_id"])
    service_state["api"]["workspace_id"] = (workspace_id or state["services"]["api"]["workspace_id"])
    service_state["api"]["scenario_id"] = scenario_id or state["services"]["api"]["scenario_id"]

    scenario_service = ScenarioService(state=service_state, azure_token=azure_token)
    response = scenario_service.delete()
    if response is None:
        return CommandResponse.fail()

    state["services"]["api"]["scenario_id"] = ""
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    logger.info(f"Scenario {service_state['api']['scenario_id']} has been successfully removed from state")
    logger.info("Scenario has been deleted")
