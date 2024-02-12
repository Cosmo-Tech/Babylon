from logging import getLogger
from typing import Any
from click import command
from click import argument
from click import option
from Babylon.commands.api.datasets.service.api import ApiDatasetService
from Babylon.utils.decorators import retrieve_state, timing_decorator, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("id", type=str)
@retrieve_state
def delete(
    state: Any,
    azure_token: str,
    id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """Delete a dataset"""
    service_state = state["services"]
    service = ApiDatasetService(azure_token=azure_token, state=service_state)
    response = service.delete(force_validation=force_validation, id=id)
    if response:
        logger.info(f"dataset id '{id}' successfully deleted")
        if "dataset.id" in state["services"]["api"]:
            if id == state["services"]["api"]["dataset.id"]:
                state["services"]["api"]["dataset.id"] = ''
                env.store_state_in_local(state=state)
                env.store_state_in_cloud(state=state)
                logger.info(f"dataset id '{id}' successfully deleted in state {state.get('id')}")
    return CommandResponse.success()
