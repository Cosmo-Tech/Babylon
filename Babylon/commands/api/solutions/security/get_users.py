import json
from logging import getLogger

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
@pass_keycloak_token()
@output_to_file
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@retrieve_state
def get_users(state: dict, organization_id: str, solution_id: str, keycloak_token: str) -> CommandResponse:
    """
    Get the Solution security users list
    """
    _sol = [""]
    _sol.append("Get solution security users list")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["solution_id"] = solution_id or service_state["api"]["solution_id"]
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"Fetching solution {[service_state['api']['solution_id']]} RBAC users")
    response = solution_service.get_users()
    if response is None:
        return CommandResponse.fail()
    users = response.json()
    logger.info(json.dumps(users, indent=2))
    return CommandResponse.success(users)
