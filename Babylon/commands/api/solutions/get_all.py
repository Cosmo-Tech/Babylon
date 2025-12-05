from logging import getLogger
from typing import Any, Optional

import jmespath
from click import argument, command, echo, option, style

from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(
    state: Any, config: Any, keycloak_token: str, organization_id: str, filter: Optional[str] = None
) -> CommandResponse:
    """
    Get all solutions details

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
    """
    _sol = [""]
    _sol.append("Get all solutions details")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    solutions_service = SolutionService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Getting all solutions from organization {[services_state['organization_id']]}")
    response = solutions_service.get_all()
    if response is None:
        return CommandResponse.fail()
    solutions = response.json()
    if len(solutions) and filter:
        solutions = jmespath.search(filter, solutions)
    logger.info(f"Retrieved solutions: {[s.get('id') for s in solutions]}")
    return CommandResponse.success(solutions)
