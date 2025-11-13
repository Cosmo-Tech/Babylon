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
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@retrieve_state
def set_default(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    solution_id: str,
    role: str = None,
) -> CommandResponse:
    """
    Set the Solution default security
    """
    _sol = [""]
    _sol.append("Set default RBAC access to the solution")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=service_state)
    details = json.dumps(obj={"role": role}, indent=2, ensure_ascii=True)
    logger.info(f"Setting default RBAC access to the solution {[service_state['api']['solution_id']]}")
    response = solution_service.set_default(details)
    if response is None:
        return CommandResponse.fail()
    default_security = response.json()
    logger.info(json.dumps(default_security, indent=2))
    logger.info(f"default RBAC access successfully set with role {[role]}")
    return CommandResponse.success(response)
