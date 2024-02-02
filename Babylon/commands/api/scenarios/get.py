from click import command, argument

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import get_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse


@command()
@wrapcontext()
@timing_decorator
@argument("scenario_id", required=False)
def get(scenario_id: str) -> CommandResponse:
    """
    Get scenario details
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
    service = ScenarioService(state)
    response = service.get()
    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(response.json(), verbose=True)
