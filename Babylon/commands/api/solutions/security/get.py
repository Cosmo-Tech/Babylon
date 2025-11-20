import json

from typing import Any
from click import option, command, echo, style
from logging import getLogger
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.commands.api.solutions.services.solutions_security_svc import SolutionSecurityService

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--email", "email", type=str, required=True, help="Email valid")
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@retrieve_state
def get(state: Any, organization_id: str, solution_id: str, keycloak_token: str, email: str) -> CommandResponse:
    """
    Get solution users RBAC access
    """
    _sol = [""]
    _sol.append("Get solution user RBAC access")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Get user {[email]} RBAC access to the solution {[service_state['api']['solution_id']]}")
    response = solution_service.get(email)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(json.dumps(rbacs, indent=2))
    return CommandResponse.success(rbacs)
