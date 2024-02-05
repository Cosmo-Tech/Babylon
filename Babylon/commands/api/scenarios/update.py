from logging import getLogger

from click import command, argument

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse

payload = {
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
}
logger = getLogger("Babylon")


@command()
@wrapcontext()
@pass_azure_token("csm_api")
@timing_decorator
@argument("scenario_id", required=False)
def update(scenario_id: str, azure_token: str) -> CommandResponse:
    """
    Update a scenario
    """
    if not scenario_id:
        logger.error("Scenario id is missing")
        return CommandResponse.fail()

    state = {
        "state": {
            "api": {
                "url": "https://dev.api.cosmotech.com",
                "organization_id": "o-3z188zr63xk",
                "workspace_id": "w-k91e49pgyw6",
                "scenario_id": scenario_id
            }
        },
    }
    spec = payload
    scenario_service = ScenarioService(state=state, spec=spec, azure_token=azure_token)
    scenario_service_response = scenario_service.update()
    if scenario_service_response is None:
        return CommandResponse.fail()
    response = scenario_service_response.json()
    return CommandResponse.success(response, verbose=True)
