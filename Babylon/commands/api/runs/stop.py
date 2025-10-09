from logging import getLogger
from typing import Any

from click import command, option

from Babylon.commands.api.runs.services.run_api_svc import RunService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import injectcontext, retrieve_state, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--run-id", "run_id", type=str)
@retrieve_state
def stop(state: Any, azure_token: str, organization_id: str, run_id: str) -> CommandResponse:
    """
    Stop the Run
    """
    service_state = state['services']
    service_state['api']['organization_id'] = organization_id or service_state['api']['organization_id']
    service_state['api']['run_id'] = run_id or service_state['api'].get('run_id')
    logger.info(f"stopping run: {service_state['api']['run_id']}")
    service = RunService(state=service_state, azure_token=azure_token)
    response = service.stop()
    if response is None:
        return CommandResponse.fail()
    stopped_run = response.json()
    return CommandResponse.success(stopped_run, verbose=True)
