from logging import getLogger
from typing import Any

from click import command, option
from Babylon.commands.api.scenarioruns.services.api import ScenarioRunService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import injectcontext, retrieve_state, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--scenariorun-id", "scenariorun_id", type=str)
@retrieve_state
def logs(state: Any, azure_token: str, organization_id: str, scenariorun_id: str) -> CommandResponse:
    """
    Get the logs for the scenarioRun
    """
    service_state = state['services']
    service_state['api']['organization_id'] = organization_id or service_state['api']['organization_id']
    service_state['api']['scenariorun_id'] = scenariorun_id or service_state['api'].get('scenariorun_id')
    logger.info(f"Getting logs for scenariorun: {service_state['api']['scenariorun_id']}")
    service = ScenarioRunService(state=service_state, azure_token=azure_token)
    response = service.logs()
    if response is None:
        return CommandResponse.fail()
    run_logs = response.json()
    return CommandResponse.success(run_logs, verbose=True)
