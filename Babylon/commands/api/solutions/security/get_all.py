import json
from logging import getLogger
from typing import Any

from click import argument, command, echo, style

from Babylon.commands.api.solutions.services.solutions_security_svc import SolutionSecurityService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
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
@retrieve_state
def get_all(
    state: Any,
    config: Any,
    organization_id: str,
    solution_id: str,
    keycloak_token: str,
) -> CommandResponse:
    """
    Get all RBAC access to the Solution

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       SOLUTION_ID : The unique identifier of the solution
    """
    _sol = [""]
    _sol.append("Get all RBAC access to the solution")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["solution_id"] = solution_id or services_state["solution_id"]
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Retrieving all RBAC access to the solution {[services_state['solution_id']]}")
    response = solution_service.get_all()
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(json.dumps(rbacs, indent=2))
    return CommandResponse.success(rbacs)
