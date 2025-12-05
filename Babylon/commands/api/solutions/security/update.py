import json
from logging import getLogger

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
@pass_keycloak_token()
@option("--email", "email", type=str, required=True, help="Email valid")
@argument("organization_id", required=True)
@argument("solution_id", required=True)
@option(
    "--role",
    "role",
    type=str,
    required=True,
    help="Role RBAC",
)
@output_to_file
@retrieve_state
def update(
    state: dict, config: dict, organization_id: str, solution_id: str, keycloak_token: str, email: str, role: str
) -> CommandResponse:
    """
    Update solution users RBAC access

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       PAYLOAD_FILE : Path to the manifest file used to update the organization
    """
    _sol = [""]
    _sol.append("Update solution user RBAC access")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["solution_id"] = solution_id or services_state["solution_id"]
    details = json.dumps({"id": email, "role": role})
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Updating user {[email]} RBAC access in the solution {[services_state['solution_id']]}")
    response = solution_service.update(id=email, details=details)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(json.dumps(rbacs, indent=2))
    logger.info(f"User {[email]} RBAC access successfully Updated")
    return CommandResponse.success(rbacs)
