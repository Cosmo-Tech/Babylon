import json
from logging import getLogger
from typing import Any

from click import command, echo, option, style

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
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@option("--runTemplate-id", "runTemplate_id", type=str, required=True, help="Run Template id")
@retrieve_state
def get(
    state: Any,
    keycloak_token: str,
    organization_id: str,
    solution_id: str,
    runTemplate_id: str,
) -> CommandResponse:
    """
    Get RunTemplate in the solution by ID
    """
    _sol = [""]
    _sol.append("Get runtemplate in solution by id")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    service_state = state["services"]
    service_state["api"]["organization_id"] = organization_id or service_state["api"]["organization_id"]
    service_state["api"]["solution_id"] = solution_id or service_state["api"]["solution_id"]
    solution_service = SolutionRunTemplatesService(keycloak_token=keycloak_token, state=service_state)
    logger.info(
        f"[api] Retrieving runtemplate id {[runTemplate_id]} in the solution {[service_state['api']['solution_id']]}"
    )
    response = solution_service.get(runTemplate_id)
    if response is None:
        return CommandResponse.fail()
    run_template = response.json()
    logger.info(json.dumps(run_template, indent=2))
    return CommandResponse.success(run_template)
