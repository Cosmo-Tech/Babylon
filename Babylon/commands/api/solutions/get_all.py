from logging import getLogger
from typing import Any, Optional

import jmespath
from click import command
from click import option

from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import wrapcontext, retrieve_state
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@wrapcontext()
@timing_decorator
@output_to_file
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@option("--filter", "filter", help="Filter response with a jmespath query")
@retrieve_state
def get_all(state: Any,
            azure_token: str,
            organization_id: str,
            solution_id: str,
            filter: Optional[str] = None) -> CommandResponse:
    """
    Get all solutions details
    """
    state = state['services']
    state['api']['organization_id'] = organization_id or state['api']['organization_id']
    state['api']['solution_id'] = solution_id or state['api']['solution_id']
    if state['api']['solution_id'] is None:
        logger.error(f"solution : {state['api']['solution_id']} does not exist")
        return CommandResponse.fail()

    logger.info(f"Getting all solutions from organization {state['api']['organization_id']}")
    service = SolutionService(state=state, azure_token=azure_token)
    response = service.get_all()
    solutions = response.json()

    if response is None:
        return CommandResponse.fail()
    if len(solutions) and filter:
        solutions = jmespath.search(filter, solutions)
    return CommandResponse.success(solutions, verbose=True)
