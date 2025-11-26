from logging import getLogger
from typing import Any
from click import command, argument, echo, style
from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import injectcontext, retrieve_config_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("solution_id", required=True)
@retrieve_config_state
def get(state: Any, config: Any, keycloak_token: str, organization_id: str, solution_id: str) -> CommandResponse:
    """
    Get a specific solution details

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       SOLUTION_ID : The unique identifier of the solution
    """ 
    _sol = [""]
    _sol.append("Get solution details")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = (organization_id or services_state["organization_id"])
    services_state["solution_id"] = (solution_id or services_state["solution_id"])
    logger.info(f"Retrieving solution {[services_state['solution_id']]} details")
    organizations_service = SolutionService(state=services_state, keycloak_token=keycloak_token, config=config)
    response = organizations_service.get()
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    return CommandResponse.success(solution)
