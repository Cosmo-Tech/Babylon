from logging import getLogger
from typing import Any

from click import command
from click import option

from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import wrapcontext, retrieve_state
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.messages import SUCCESS_DELETED
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@retrieve_state
def delete(state: Any, azure_token: str, organization_id: str, solution_id: str,
           force_validation: bool = False) -> CommandResponse:
    """
    Delete a solution
    """
    state = state['state']
    state['api']['organization_id'] = organization_id or state['api']['organization_id']
    state['api']['solution_id'] = solution_id or state['api']['solution_id']

    if not force_validation and not confirm_deletion("solution", solution_id):
        return CommandResponse.fail()

    logger.info(f"Deleting solution: {state['api']['solution_id']}")
    service = SolutionService(state=state, azure_token=azure_token)
    response = service.delete()

    if response is None:
        return CommandResponse.fail()
    logger.info(SUCCESS_DELETED("solution", solution_id))
    return CommandResponse.success()
