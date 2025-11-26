import json
import pathlib

from typing import Any
from click import command, argument, echo, style
from click import Path
from logging import getLogger
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import retrieve_config_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.commands.api.solutions.services.solutions_runtemplates_svc import SolutionRunTemplatesService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("solution_id", required=True)
@argument("runTemplate_id", required=True)
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_config_state
def update(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    solution_id: str,
    runTemplate_id: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Update Run Template in the Solution by id

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       SOLUTION_ID : The unique identifier of the solution
       RUNTEMPLATE_ID: The unique identifier of the runTemplate
       PAYLOAD_FILE : Path to the manifest file used to add the runTemplates
    """
    _sol = [""]
    _sol.append("Update solution RunTemplate")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    spec = dict()
    services_state = state["services"]["api"]
    services_state["organization_id"] = (organization_id or services_state["organization_id"])
    services_state["solution_id"] = (solution_id or services_state["solution_id"])
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    solution_service = SolutionRunTemplatesService(keycloak_token=keycloak_token,
                                                   state=services_state,
                                                   spec=spec,
                                                   config=config)
    logger.info(f"[api] Updating runtemplate in the solution {[services_state['solution_id']]}")
    response = solution_service.update(runTemplate_id)
    if response is None:
        return CommandResponse.fail()
    run_template = response.json()
    logger.info(json.dumps(run_template, indent=2))
    sol_id = services_state['solution_id']
    logger.info(f"[api] Runtemplate id {[run_template.get('id')]} successfully updated in the solution {[sol_id]}")
    return CommandResponse.success(run_template)
