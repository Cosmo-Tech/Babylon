import pathlib

from logging import getLogger
from typing import Any
from click import Path
from click import argument
from click import command
from click import option
from Babylon.commands.api.solutions.services.solutions_api_svc import SolutionService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@argument("payload_file", type=Path(path_type=pathlib.Path))
@retrieve_state
def create(state: Any, azure_token: str, organization_id: str, payload_file: pathlib.Path) -> CommandResponse:
    """
    Register a new solution
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    if not payload_file.exists():
        print(f"file {payload_file} not found in directory")
        return CommandResponse.fail()
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template(data=f.read(), state=state)
    service = SolutionService(azure_token=azure_token, state=service_state, spec=spec)
    response = service.create()
    solution = response.json()
    state["services"]["api"]["solution_id"] = solution.get("id")
    env.store_state_in_local(state)
    if env.remote:
        env.store_state_in_cloud(state)
    logger.info(f"Solution {solution.get('id')} successfully saved in state {state.get('id')}")
    return CommandResponse.success(solution, verbose=True)
