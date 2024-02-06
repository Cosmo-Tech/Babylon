from logging import getLogger
from typing import Any

from click import command, option

from Babylon.commands.api.scenarioruns.service.api import ScenarioRunService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext, retrieve_state
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = getLogger("Babylon")


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@option("--org-id", "organization_id", type=QueryType())
@option("--scenariorun-id", "scenariorun_id", type=QueryType())
@retrieve_state
def status(state: Any, azure_token: str, organization_id: str, scenariorun_id: str) -> CommandResponse:
    """
    Get the status of the scenarioRun
    """
    state = state['state']
    state['api']['organization_id'] = organization_id or state['api']['organization_id']
    state['api']['scenariorun_id'] = scenariorun_id or state['api']['scenariorun_id']

    logger.info(f"Getting status for scenariorun: {state['api']['scenariorun_id']}")
    service = ScenarioRunService(state=state, azure_token=azure_token)
    response = service.status()

    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(response.json(), verbose=True)
