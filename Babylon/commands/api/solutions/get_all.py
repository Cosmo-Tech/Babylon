import jmespath
from logging import getLogger
from typing import Any, Optional
from click import command, option, echo, style
from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any, keycloak_token: str, organization_id: str, filter: Optional[str] = None) -> CommandResponse:
    """
    Get all solutions details
    """
    _sol = [""]
    _sol.append("Get all solutions details")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    solutions_service = SolutionService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Getting all solutions from organization {[service_state['api']['organization_id']]}")
    response = solutions_service.get_all()
    if response is None:
        return CommandResponse.fail()
    solutions = response.json()
    if len(solutions) and filter:
        solutions = jmespath.search(filter, solutions)
    logger.info(f"Retrieved solutions: {[s.get('id') for s in solutions]}")
    return CommandResponse.success(solutions)
