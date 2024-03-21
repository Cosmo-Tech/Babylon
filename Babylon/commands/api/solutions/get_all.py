import jmespath

from logging import getLogger
from typing import Any, Optional
from click import command
from click import option
from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, azure_token: str, organization_id: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all solutions details
    """
    service_state = state["services"]
    logger.info(f"Getting all solutions from organization {service_state['api']['organization_id']}")
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service = SolutionService(azure_token=azure_token, state=service_state)
    response = service.get_all()
    if response is None:
        return CommandResponse.fail()
    solutions = response.json()
    if len(solutions) and filter:
        solutions = jmespath.search(filter, solutions)
    return CommandResponse.success(solutions, verbose=True)
