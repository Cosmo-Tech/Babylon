import json

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
@option("--email", "email", type=str, required=True, help="Email valid")
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@output_to_file
@retrieve_state
def update(state: dict, organization_id: str, solution_id: str, keycloak_token: str, email: str,
           role: str) -> CommandResponse:
    """
    Update solution users RBAC access
    """
    _sol = [""]
    _sol.append("Update solution user RBAC access")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])
    details = json.dumps({"id": email, "role": role})
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Updating user {[email]} RBAC access in the solution {[service_state['api']['solution_id']]}")
    response = solution_service.update(id=email, details=details)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(json.dumps(rbacs, indent=2))
    logger.info(f"[api] User {[email]} RBAC access successfully Updated")
    return CommandResponse.success(rbacs)
