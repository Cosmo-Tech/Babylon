import pathlib
from logging import getLogger
from typing import Any

from click import Path, argument, command, echo, style

from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.utils.credentials import pass_keycloak_token
from Babylon.utils.decorators import injectcontext, output_to_file, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_keycloak_token()
@argument("organization_id", required=True)
@argument("payload_file", type=Path(path_type=pathlib.Path, exists=True))
@retrieve_state
def create(
    state: Any, config: Any, keycloak_token: str, organization_id: str, payload_file: pathlib.Path
) -> CommandResponse:
    """
    Register a new solution

    Args:

       ORGANIZATION_ID : The unique identifier of the organization
       PAYLOAD_FILE : Path to the manifest file used to update the solution
    """
    _sol = [""]
    _sol.append("Register new solution")
    _sol.append("")
    echo(style("\n".join(_sol), bold=True, fg="green"))
    services_state = state["services"]["api"]
    services_state["organization_id"] = organization_id or services_state["organization_id"]
    spec = dict()
    with open(payload_file, "r") as f:
        spec["payload"] = env.fill_template_jsondump(data=f.read(), state=state)
    solutions_service = SolutionService(keycloak_token=keycloak_token, state=services_state, config=config, spec=spec)
    logger.info("Creating solution")
    response = solutions_service.create()
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    logger.info(f"Solution {[solution.get('id')]} successfully created")
    return CommandResponse.success(solution)
