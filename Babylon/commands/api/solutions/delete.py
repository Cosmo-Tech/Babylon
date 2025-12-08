from logging import getLogger
from typing import Any

from click import argument, command, echo, option, style

from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("solution_id", required=True)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@retrieve_state
def delete(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    solution_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a specific solution

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       SOLUTION_ID : The unique identifier of the solution
    """
    _sol = [""]
    _sol.append("Delete solution")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["solution_id"] = solution_id or services_state["solution_id"]
    solutions_service = SolutionService(state=services_state, keycloak_token=keycloak_token, config=config)
    logger.info("Deleting solution")
    response = solutions_service.delete(force_validation=force_validation)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Solution {[services_state['solution_id']]} successfully deleted")
    return CommandResponse.success(response)
