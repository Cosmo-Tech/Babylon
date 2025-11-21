import json
from logging import getLogger
from typing import Any

from click import command, echo, option, style

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
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@retrieve_state
def get_all(
    state: Any,
    organization_id: str,
    solution_id: str,
    keycloak_token: str,
) -> CommandResponse:
    """
    Get all RBAC access to the Solution
    """
    _sol = [""]
    _sol.append("Get all RBAC access to the solution")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["solution_id"] = solution_id or service_state["api"]["solution_id"]
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Retrieving all RBAC access to the solution {[service_state['api']['solution_id']]}")
    response = solution_service.get_all()
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(json.dumps(rbacs, indent=2))
    return CommandResponse.success(rbacs)
