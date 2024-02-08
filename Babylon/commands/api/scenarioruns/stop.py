from logging import getLogger
from typing import Any

from click import command, option

from Babylon.commands.api.scenarioruns.service.api import ScenarioRunService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator, wrapcontext, retrieve_state
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--scenariorun-id", "scenariorun_id", type=str)
@retrieve_state
def stop(state: Any, azure_token: str, organization_id: str, scenariorun_id: str) -> CommandResponse:
    """
    Stop the scenarioRun
    """
    state = state['state']
    state['api']['organization_id'] = organization_id or state['api']['organization_id']
    state['api']['scenariorun_id'] = scenariorun_id or state['api'].get('scenariorun_id')
    if state['api']['scenariorun_id'] is None:
        return CommandResponse.fail()

    logger.info(f"stopping scenariorun: {state['api']['scenariorun_id']}")
    service = ScenarioRunService(state=state, azure_token=azure_token)
    response = service.stop()

    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(response.json(), verbose=True)
