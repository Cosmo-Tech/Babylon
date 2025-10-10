import json
import click

from typing import Any
from click import command, option
from logging import getLogger
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.commands.api.solutions.services.solutions_runtemplates_svc import SolutionRunTemplatesService

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@retrieve_state
def get_all(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    solution_id: str,
) -> CommandResponse:
    """
    Get all RunTemplates in solution 
    """
    _ret = [""]
    _ret.append("Get all runtemplates in solution")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])
    solution_service = SolutionRunTemplatesService(keycloak_token=keycloak_token, state=service_state)
    logger.info(f"[api] Retrieving all runtemplates in the solution {[service_state['api']['solution_id']]}")
    response = solution_service.get_all()
    if response is None:
        return CommandResponse.fail()
    run_templates = response.json()
    logger.info(json.dumps(run_templates, indent=2))
    return CommandResponse.success(run_templates)
