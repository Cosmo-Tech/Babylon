import json
import click
import pathlib

from typing import Any
from click import argument, option, command
from click import Path
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
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_state
def add(
    state: Any,
    keycloak_token: str,
    payload_file: pathlib.Path,
    organization_id: str,
    solution_id: str,
) -> CommandResponse:
    """
    Add runTemplates to solution
    """
    _ret = [""]
    _ret.append("Add runtemplates to solution")
    _ret.append("")
    click.echo(click.style("\n".join(_ret), bold=True, fg="green"))
    spec = dict()
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    solution_service = SolutionRunTemplatesService(keycloak_token=keycloak_token, state=service_state, spec=spec)
    logger.info(f"[api] Adding runtemplates to the solution {[service_state['api']['solution_id']]}")
    response = solution_service.add()
    if response is None:
        return CommandResponse.fail()
    run_template = response.json()
    logger.info(json.dumps(run_template, indent=2))
    sol_id = service_state['api']['solution_id']
    logger.info(f"[api] Run Templates id:{[run_template.get('id')]} successfully added to the solution {[sol_id]}")
    return CommandResponse.success(run_template)
