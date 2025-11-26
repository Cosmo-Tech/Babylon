from click import option, command, echo, style, argument
from logging import getLogger
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file, retrieve_config_state
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
@option("--email", "email", type=str, required=True, help="Email valid")
@argument("organization_id", required=True)
@argument("solution_id", required=True)
@retrieve_config_state
def delete(state: dict, config: dict, organization_id: str, solution_id: str, keycloak_token: str, email: str) -> CommandResponse:
    """
    Remove the specified access from the Solution

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       SOLUTION_ID : The unique identifier of the solution
    """
    _sol = [""]
    _sol.append("Delete solution users RBAC access")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["solution_id"] = (solution_id or services_state["solution_id"])
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"Deleting user {[email]} RBAC permissions on solution {[services_state['solution_id']]}")
    response = solution_service.delete(email)
    if response is None:
        return CommandResponse.fail()
    logger.info("User RBAC permissions successfully deleted")
    return CommandResponse.success(response)
