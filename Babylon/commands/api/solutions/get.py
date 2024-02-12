from logging import getLogger
from typing import Any

from click import command, option

from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import wrapcontext, retrieve_state
from Babylon.utils.environment import Environment
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
@retrieve_state
def get(state: Any, azure_token: str, organization_id: str, solution_id: str) -> CommandResponse:
    """
    Get a solution details
    """
    state = state['services']
    state['api']['organization_id'] = organization_id or state['api']['organization_id']
    state['api']['solution_id'] = solution_id or state['api']['solution_id']
    if state['api']['solution_id'] is None:
        logger.error(f"solution : {state['api']['solution_id']} does not exist")
        return CommandResponse.fail()

    logger.info(f"Searching solution: {state['api']['solution_id']}")
    service = SolutionService(state=state, azure_token=azure_token)
    response = service.get()
    solution = response.json()

    if response is None:
        return CommandResponse.fail()
    return CommandResponse.success(solution, verbose=True)
