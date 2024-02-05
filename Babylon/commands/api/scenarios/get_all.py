from click import command

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse


@command()
@wrapcontext()
@pass_azure_token("csm_api")
@timing_decorator
def get_all(azure_token: str) -> CommandResponse:
    """
    Get all scenarios in the workspace
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
    scenario_service = ScenarioService(state=state, azure_token=azure_token)
    scenario_service_response = scenario_service.get_all()
    if scenario_service_response is None:
        return CommandResponse.fail()
    response = scenario_service_response.json()
    return CommandResponse.success(response, verbose=True)
