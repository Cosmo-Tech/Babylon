import json
import pathlib

from typing import Any
from click import argument, command, Path, echo, style
from logging import getLogger
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_config_state, injectcontext, output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.commands.api.solutions.services.solutions_runtemplates_svc import SolutionRunTemplatesService

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("solution_id", required=True)
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_config_state
def add(
    state: Any,
    config: Any,
    keycloak_token: str,
    payload_file: pathlib.Path,
    organization_id: str,
    solution_id: str,
) -> CommandResponse:
    """
    Add runTemplates to solution

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       SOLUTION_ID : The unique identifier of the solution
       PAYLOAD_FILE : Path to the manifest file used to add the runTemplates
    """
    _sol = [""]
    _sol.append("Add runtemplates to solution")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    spec = dict()
    services_state = state["services"]["api"]
    services_state["organization_id"] = (organization_id or services_state["organization_id"])
    services_state["solution_id"] = (solution_id or services_state["solution_id"])
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    solution_service = SolutionRunTemplatesService(keycloak_token=keycloak_token, state=services_state, spec=spec, config=config)
    logger.info(f"Adding runtemplates to the solution {[services_state['solution_id']]}")
    response = solution_service.add()
    if response is None:
        return CommandResponse.fail()
    run_template = response.json()
    logger.info(json.dumps(run_template, indent=2))
    sol_id = services_state['solution_id']
    logger.info(f"Run Templates id {[run_template.get('id')]} successfully added to the solution {[sol_id]}")
    return CommandResponse.success(run_template)
