from typing import Any
from click import command, argument, echo, style
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
@retrieve_config_state
def get_all(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    solution_id: str,
) -> CommandResponse:
    """
    Get all RunTemplates in solution

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       SOLUTION_ID : The unique identifier of the solution
    """
    _sol = [""]
    _sol.append("Get all runtemplates in solution")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = (organization_id or services_state["organization_id"])
    services_state["solution_id"] = (solution_id or services_state["solution_id"])
    solution_service = SolutionRunTemplatesService(keycloak_token=keycloak_token, state=services_state, config=config)
    response = solution_service.get_all()
    if response is None:
        return CommandResponse.fail()
    run_templates = response.json()
    logger.info(f"Retrieving all runtemplates in the solution {[services_state['solution_id']]}")
    return CommandResponse.success(run_templates)
