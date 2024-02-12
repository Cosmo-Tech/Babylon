import pathlib

from logging import getLogger
from typing import Any
from click import Path, argument
from click import command
from click import option
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
@argument("payload", type=Path(path_type=pathlib.Path))
@retrieve_state
def update(
    state: Any,
    azure_token: str,
    organization_id: str,
    solution_id: str,
    payload: pathlib.Path,
) -> CommandResponse:
    """
    Update a solution
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])
    spec = dict()
    spec["payload"] = payload
    service = SolutionService(state=service_state, azure_token=azure_token, spec=spec)
    response = service.update()
    if response is None:
        return CommandResponse.fail()
    solution = response.json()
    if response:
        logger.info(f'Solution {service_state["api"]["solution_id"]} successfully updated')
        if (service_state["api"]["solution_id"] == state["services"]["api"]["solution_id"]):
            logger.info(
                f'Solution {state["services"]["api"]["solution_id"]} stored in state has been successfully updated')
    return CommandResponse.success(solution, verbose=True)
