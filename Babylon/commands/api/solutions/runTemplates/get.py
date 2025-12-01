import json
from logging import getLogger
from typing import Any

from click import argument, command, echo, style

from Babylon.commands.api.solutions.services.solutions_runtemplates_svc import SolutionRunTemplatesService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config_state
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
@retrieve_config_state
def get(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    solution_id: str,
    runTemplate_id: str,
) -> CommandResponse:
    """
    Get RunTemplate in the solution by ID

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       SOLUTION_ID : The unique identifier of the solution
       PAYLOAD_FILE : Path to the manifest file used to add the runTemplates
    """
    _sol = [""]
    _sol.append("Get runtemplate in solution by id")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["solution_id"] = solution_id or services_state["solution_id"]
    solution_service = SolutionRunTemplatesService(keycloak_token=keycloak_token, state=services_state, config=config)
    logger.info(f"[api] Retrieving runtemplate id {[runTemplate_id]} in the solution {[services_state['solution_id']]}")
    response = solution_service.get(runTemplate_id)
    if response is None:
        return CommandResponse.fail()
    run_template = response.json()
    logger.info(json.dumps(run_template, indent=2))
    return CommandResponse.success(run_template)
