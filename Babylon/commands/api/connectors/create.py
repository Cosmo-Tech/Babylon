import logging
import pathlib

from typing import Any, Optional
from click import Path
from click import command
from click import option
from Babylon.commands.api.connectors.service.api import ApiConnectorService
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_azure_token("csm_api")
@option("--payload",
        "connector_file",
        type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
        help="Your custom connector description file (yaml or json)")
@output_to_file
@retrieve_state
def create(
    state: Any,
    azure_token: str,
    connector_file: Optional[pathlib.Path] = None,
) -> CommandResponse:
    """
    Register new Connector
    """
    service_state = state["services"]
    service = ApiConnectorService(azure_token=azure_token, state=service_state)
    response = service.create(connector_file=connector_file)
    if response:
        state["services"]["api"]["connector.id"] = response.get("id")
        env.store_state_in_local(state=state)
        env.store_state_in_cloud(state=state)
        logger.info(f"connector id '{response.get('id')}' successfully saved in state {state.get('id')}")
    return CommandResponse.success(response, verbose=True)
