from click import command

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse

payload = {
    "name": "Creating scenario with Babylon",
    "description": "Brewery master reference analysis",
    "tags": ["Brewery", "reference"],
    "runTemplateId": "hundred",
    "security": {
        "default": "viewer",
        "accessControlList": [{
            "id": "elena.sasova@cosmotech.com",
            "role": "admin"
        }],
    },
}


@command()
@wrapcontext()
@pass_azure_token("csm_api")
@timing_decorator
def create(azure_token: str) -> CommandResponse:
    """
    Create new scenario
    """

    state = {
        "state": {
            "api": {
                "url": "https://dev.api.cosmotech.com",
                "organization_id": "o-3z188zr63xk",
                "workspace_id": "w-k91e49pgyw6",
            }
        },
    }
    spec = payload

    scenario_service = ScenarioService(state=state, azure_token=azure_token, spec=spec)
    scenario_service_response = scenario_service.create()
    if scenario_service_response is None:
        return CommandResponse.fail()
    response = scenario_service_response.json()
    return CommandResponse.success(response, verbose=True)
