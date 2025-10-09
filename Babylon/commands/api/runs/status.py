from logging import getLogger
from typing import Any
from click import command, option
from Babylon.commands.api.runs.services.run_api_svc import RunService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state, output_to_file
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--run-id", "run_id", type=str)
@retrieve_state
def status(state: Any, keycloak_token: str, organization_id: str, run_id: str) -> CommandResponse:
    """
    Get the status of the Run
    """
    service_state = state['services']
    service_state['api']['organization_id'] = organization_id or service_state['api']['organization_id']
    service_state['api']['run_id'] = run_id or service_state['api'].get('run_id')
    logger.info(f"Getting status for run: {service_state['api']['run_id']}")
    service = RunService(state=service_state, keycloak_token=keycloak_token)
    response = service.status()
    if response is None:
        return CommandResponse.fail()
    run_status = response.json()
    return CommandResponse.success(run_status, verbose=True)
