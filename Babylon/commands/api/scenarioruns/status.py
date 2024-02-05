import json
from logging import getLogger

from click import command, option

from Babylon.commands.api.scenarioruns.service.api import ScenarioRunService
from Babylon.utils.credentials import get_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = getLogger("Babylon")
payload = json.dumps({
    "organization_id": "",
    "scenariorun_id": ""
})


@command()
@wrapcontext()
@timing_decorator
@option("--org-id", "organization_id", type=QueryType())
@option("--scenariorun-id", "scenariorun_id", type=QueryType())
def status(organization_id: str, scenariorun_id: str) -> CommandResponse:
    """
    Get the status of the scenarioRun
    """
    token = get_azure_token("csm_api")

    state = {
        "api_url": "https://dev.api.cosmotech.com",
        "organization_id": "o-3z188zr63xk",
        "scenariorun_id": ""
    }
    state['state']['api']['organization_id'] = organization_id or state['state']['api']['organization_id']
    state['state']['api']['scenariorun_id'] = scenariorun_id or state['state']['api']['scenariorun_id']

    logger.info(f"Getting status for scenariorun: {state['state']['api']['scenariorun_id']}")
    service = ScenarioRunService(state=state, azure_token=token)
    response = service.status()

    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(response.json(), verbose=True)
