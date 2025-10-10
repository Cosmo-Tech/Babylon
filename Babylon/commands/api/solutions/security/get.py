import json
import click

from typing import Any
from click import option
from click import command
from logging import getLogger
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.commands.api.solutions.services.solutions_security_svc import SolutionSecurityService

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--email", "email", type=str, required=True, help="Email valid")
@retrieve_state
def get(state: Any, keycloak_token: str, email: str) -> CommandResponse:
    """
    Get solution users RBAC access
    """
    _ret = [""]
    _ret.append("Get solution user RBAC access")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    solution_service = SolutionSecurityService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Get user {[email]} RBAC access to the solution {[service_state['api']['solution_id']]}")
    response = solution_service.get(email)
    if response is None:
        return CommandResponse.fail()
    rbacs = response.json()
    logger.info(json.dumps(rbacs, indent=2))
    return CommandResponse.success(rbacs)
