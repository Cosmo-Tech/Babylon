import pathlib
import json
import click

from logging import getLogger
from typing import Any
from click import Path
from click import argument
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
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_state
def create(state: Any, keycloak_token: str, organization_id: str, payload_file: pathlib.Path) -> CommandResponse:
    """
    Register a new solution
    """
    _ret = [""]
    _ret.append("Register new organization")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    solutions_service = SolutionService(keycloak_token=keycloak_token, state=service_state, spec=spec)
    logger.info("[api] Creating solution")
    response = solutions_service.create()
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    state["services"]["api"]["solution_id"] = solution.get("id")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    logger.info(json.dumps(solution, indent=2))
    logger.info(f"[api] Solution {solution.get('id')} successfully created")
    return CommandResponse.success(solution)
