from logging import getLogger

from click import command, argument

from Babylon.commands.api.scenarios.service.api import ScenarioService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@wrapcontext()
@pass_azure_token("csm_api")
@timing_decorator
@argument("scenario_id", required=False)
def run(scenario_id: str, azure_token: str) -> CommandResponse:
    """
    Start a scenario run
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
    scenario_service = ScenarioService(state, azure_token=azure_token)
    scenario_service_response = scenario_service.run()
    if scenario_service_response is None:
        return CommandResponse.fail()
    response = scenario_service_response.json()
    return CommandResponse.success(response, verbose=True)
