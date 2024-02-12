import pathlib
from logging import getLogger
from typing import Any

from click import Path
from click import command
from click import option

from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import wrapcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS_UPDATED
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@option(
    "--file",
    "solution_file",
    type=Path(path_type=pathlib.Path),
    help="Your custom solution description file yaml", )
@retrieve_state
def update(state: Any, azure_token: str, organization_id: str, solution_id: str, solution_file:
           pathlib.Path) -> CommandResponse:
    """
    Update a solution
    """
    state = state['state']
    state['api']['organization_id'] = organization_id or state['api']['organization_id']
    state['api']['solution_id'] = solution_id or state['api']['solution_id']
    if state['api']['solution_id'] is None:
        logger.error(f"solution : {state['api']['solution_id']} does not exist")
        return CommandResponse.fail()

    path_file = f"{env.context_id}.{env.environ_id}.solution.yaml"
    solution_file = solution_file or env.working_dir.payload_path / path_file
    if not solution_file.exists():
        return CommandResponse.fail()
    details = env.fill_template(solution_file)
    spec = {"data": details}

    service = SolutionService(state=state, azure_token=azure_token, spec=spec)
    response = service.get()
    updated_solution = response.json()

    if response is None:
        return CommandResponse.fail()
    logger.info(SUCCESS_UPDATED("solution", solution_id))
    return CommandResponse.success(updated_solution, verbose=True)
