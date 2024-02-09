import logging

from typing import Any
from click import argument
from click import command
from click import option
from Babylon.commands.api.connectors.service.api import ApiConnectorService
from Babylon.utils.decorators import retrieve_state, timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
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
    """Delete a registered connector"""
    service_state = state["services"]
    service = ApiConnectorService(azure_token=azure_token, state=service_state)
    service.delete(force_validation=force_validation, id=id)
    if "connector.id" in state["services"]["api"]:
        state["services"]["api"]["connector.id"] = ''
    env.store_state_in_local(state=state)
    env.store_state_in_cloud(state=state)
    logger.info(f"connector id '{id}' successfully deleted in state {state.get('id')}")
    return CommandResponse.success()
