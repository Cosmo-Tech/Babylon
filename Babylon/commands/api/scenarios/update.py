import json
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
@retrieve_state
@pass_azure_token("csm_api")
@timing_decorator
@option("--organization_id", "organization_id", type=str)
@option("--workspace_id", "workspace_id", type=str)
@argument("scenario_id", required=False)
def update(
    state: Any,
    organization_id: str,
    workspace_id: str,
    scenario_id: str,
    azure_token: str,
) -> CommandResponse:
    """
    Update a scenario
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
    service_state["api"]["scenario_id"] = scenario_id

    # change this line when scenario manipulation is specified
    spec = json.dumps({
        "parametersValues": [
            {
                "parameterId": "stock",
                "value": "6000",
                "varType": "int"
            },
            {
                "parameterId": "restock_qty",
                "value": "25",
                "varType": "int"
            },
            {
                "parameterId": "nb_waiters",
                "value": "5",
                "varType": "int"
            },
        ]
    })
    scenario_service = ScenarioService(state=service_state, spec=spec, azure_token=azure_token)
    response = scenario_service.update()
    if response is None:
        return CommandResponse.fail()
    scenario = response.json()
    return CommandResponse.success(scenario, verbose=True)
