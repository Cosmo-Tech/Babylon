from logging import getLogger
from typing import Any

from click import command, argument, option

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext, retrieve_state
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@wrapcontext()
@pass_azure_token("csm_api")
@timing_decorator
@retrieve_state
@option("--organization_id", "organization_id", type=str)
@option("--workspace_id", "workspace_id", type=str)
@argument("scenario_id", required=False)
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
    if not scenario_id:
        logger.error("Scenario id is missing")
        return CommandResponse.fail()
    service_state = state["state"]
    if organization_id:
        service_state["api"]["organization_id"] = organization_id
    if workspace_id:
        service_state["api"]["workspace_id"] = workspace_id

    # change this line when scenario manipulation is specified
    spec = {"scenario_id": scenario_id}

    scenario_service = ScenarioService(state=service_state, azure_token=azure_token, spec=spec)
    response = scenario_service.delete()
    if response is None:
        return CommandResponse.fail()
    logger.info("Scenario has been deleted")
