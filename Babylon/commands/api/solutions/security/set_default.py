import json
from logging import getLogger
from typing import Any

from click import argument, command, echo, option, style

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
    config: Any,
    keycloak_token: str,
    organization_id: str,
    solution_id: str,
    role: str = None,
) -> CommandResponse:
    """
    Set the Solution default security

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       SOLUTION_ID : The unique identifier of the solution
    """
    _sol = [""]
    _sol.append("Set default RBAC access to the solution")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["solution_id"] = solution_id or services_state["solution_id"]
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    details = json.dumps(obj={"role": role}, indent=2, ensure_ascii=True)
    logger.info(f"Setting default RBAC access to the solution {[services_state['solution_id']]}")
    response = solution_service.set_default(details)
    if response is None:
        return CommandResponse.fail()
    default_security = response.json()
    logger.info(json.dumps(default_security, indent=2))
    logger.info(f"default RBAC access successfully set with role {[role]}")
    return CommandResponse.success(response)
