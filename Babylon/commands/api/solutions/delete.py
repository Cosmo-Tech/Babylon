from logging import getLogger
from typing import Any
from Babylon.utils.environment import Environment
from click import command
from click import option
from Babylon.commands.api.solutions.service.api import SolutionService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_azure_token("csm_api")
@option("--organization-id", "organization_id", type=str)
@option("--solution-id", "solution_id", type=str)
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@retrieve_state
def delete(
    state: Any,
    azure_token: str,
    organization_id: str,
    solution_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """
    Delete a solution
    """
    service_state = state["services"]
    service_state["api"]["organization_id"] = (organization_id or service_state["api"]["organization_id"])
    service_state["api"]["solution_id"] = (solution_id or service_state["api"]["solution_id"])

    service = SolutionService(state=service_state, azure_token=azure_token)
    logger.info(f"Deleting solution: {service_state['api']['solution_id']}")
    response = service.delete(force_validation=force_validation, )
    if response:
        logger.info(f'Solution {service_state["api"]["solution_id"]} successfully deleted')
        if (service_state["api"]["solution_id"] == state["services"]["api"]["solution_id"]):
            state["services"]["api"]["solution_id"] = ""
            env.store_state_in_local(state)
            env.store_state_in_cloud(state)
            logger.info(
                f'Solution {state["services"]["api"]["solution_id"]} successfully deleted in state {state.get("id")}')
    return CommandResponse.success()
