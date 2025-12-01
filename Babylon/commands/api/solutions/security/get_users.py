import json
from logging import getLogger

from click import argument, command, echo, style

from Babylon.commands.api.solutions.services.solutions_security_svc import SolutionSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@argument("organization_id", required=True)
@argument("solution_id", required=True)
@retrieve_config_state
def get_users(
    state: dict, config: dict, organization_id: str, solution_id: str, keycloak_token: str
) -> CommandResponse:
    """
    Get the Solution security users list

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       SOLUTION_ID : The unique identifier of the solution
    """
    _sol = [""]
    _sol.append("Get solution security users list")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["solution_id"] = solution_id or services_state["solution_id"]
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Fetching solution {[services_state['solution_id']]} RBAC users")
    response = solution_service.get_users()
    if response is None:
        return CommandResponse.fail()
    users = response.json()
    logger.info(json.dumps(users, indent=2))
    return CommandResponse.success(users)
