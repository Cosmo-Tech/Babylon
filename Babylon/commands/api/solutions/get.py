import json
import click

from logging import getLogger
from typing import Any
from click import command, option
from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@retrieve_state
def get(state: Any, keycloak_token: str, organization_id: str, solution_id: str) -> CommandResponse:
    """
    Get a solution details
    """
    _ret = [""]
    _ret.append("Get solution details")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])
    logger.info(f"[api] Retrieving solution {service_state['api']['solution_id']}")
    organizations_service = SolutionService(state=service_state, keycloak_token=keycloak_token)
    response = organizations_service.get()
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    logger.info(json.dumps(solution, indent=2))
    return CommandResponse.success(solution)
