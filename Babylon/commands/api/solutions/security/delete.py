from click import option, command, echo, style
from logging import getLogger
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file, retrieve_state
from Babylon.commands.api.solutions.services.solutions_security_svc import SolutionSecurityService

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_keycloak_token()
@output_to_file
@option("--email", "email", type=str, required=True, help="Email valid")
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@retrieve_state
def delete(state: dict, organization_id: str, solution_id: str, keycloak_token: str, email: str) -> CommandResponse:
    """
    Remove the specified access from the Solution
    """
    _sol = [""]
    _sol.append("Delete solution users RBAC access")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Deleting user {[email]} RBAC permissions on solution {[service_state['api']['solution_id']]}")
    response = solution_service.delete(email)
    if response is None:
        return CommandResponse.fail()
    logger.info("[api] User RBAC permissions successfully deleted")
    return CommandResponse.success(response)
