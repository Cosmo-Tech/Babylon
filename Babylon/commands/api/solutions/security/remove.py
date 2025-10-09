import click

from click import option, command
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
@retrieve_state
def remove(state: dict, keycloak_token: str, email: str) -> CommandResponse:
    """
    Remove the specified access from the Solution
    """
    _ret = [""]
    _ret.append("Delete solution users RBAC access")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Deleting user {email} RBAC permissions on solution {service_state['api']['solution_id']}")
    response = solution_service.remove(email)
    if response is None:
        return CommandResponse.fail()
    logger.info("[api] User RBAC permissions successfully deleted")
    return CommandResponse.success(response)
