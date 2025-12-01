import pathlib
from logging import getLogger
from typing import Any

from click import Path, argument, command, echo, style

from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_config_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

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
def update(
    state: Any,
    config: Any,
    keycloak_token: str,
    organization_id: str,
    solution_id: str,
    payload_file: pathlib.Path,
) -> CommandResponse:
    """
    Update a specific solution

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       SOLUTION_ID : The unique identifier of the solution
       PAYLOAD_FILE : Path to the manifest file used to update the solution
    """
    _sol = [""]
    _sol.append("Update an solution")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    services_state["solution_id"] = solution_id or services_state["solution_id"]
    spec = dict()
    with open(payload_file, "r") as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    solutions_service = SolutionService(state=services_state, keycloak_token=keycloak_token, spec=spec, config=config)
    logger.info(f"Updating solution {[services_state['solution_id']]}")
    response = solutions_service.update()
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    logger.info(f"Solution {[services_state['solution_id']]} successfully updated")
    return CommandResponse.success(solution)
