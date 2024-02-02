import json

from click import command, argument

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import get_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse

payload = json.dumps({
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


@command()
@wrapcontext()
@timing_decorator
@argument("scenario_id", required=False)
def update(scenario_id: str) -> CommandResponse:
    """
    Update a scenario
    """
    token = get_azure_token("csm_api")
    scenario_id = scenario_id or "s-43gl934nn2"
    state = {
        "api_url": "https://dev.api.cosmotech.com",
        "organizationId": "o-3z188zr63xk",
        "workspaceId": "w-k91e49pgyw6",
        "scenario_id": scenario_id,
        "azure_token": token,
    }
    spec = payload
    service = ScenarioService(state, spec)
    response = service.update()
    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(response.json(), verbose=True)
