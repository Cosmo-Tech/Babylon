import json
import click

from click import command
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
@retrieve_state
def get_users(state: dict, keycloak_token: str) -> CommandResponse:
    """
    Get the Solution security users list
    """
    _ret = [""]
    _ret.append("Get solution security users list")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Fetching solution {[service_state['api']['solution_id']]} RBAC users")
    response = solution_service.get_users()
    if response is None:
        return CommandResponse.fail()
    users = response.json()
    logger.info(json.dumps(users, indent=2))
    return CommandResponse.success(users)
