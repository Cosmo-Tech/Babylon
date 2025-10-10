import pathlib
import json
import click

from logging import getLogger
from typing import Any
from click import Path, argument
from click import command
from click import option
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
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_state
def update(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    solution_id: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Update a solution
    """
    _ret = [""]
    _ret.append("Update an solution")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    solutions_service = SolutionService(state=service_state, keycloak_token=keycloak_token, spec=spec)
    logger.info(f"[api] Updating solution {[state['services']['api']['solution_id']]}")
    response = solutions_service.update()
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    logger.info(json.dumps(solution, indent=2))
    logger.info(f"[api] Solution {[service_state['api']['solution_id']]} successfully updated")
    return CommandResponse.success(solution)
