import logging
import pathlib

from typing import Any
from click import Path, argument
from click import command
from Babylon.commands.api.connectors.service.api import (
    ConnectorService, )
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import output_to_file
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_azure_token("csm_api")
@argument("payload_file", type=Path(path_type=pathlib.Path))
@output_to_file
@retrieve_state
def create(state: Any, azure_token: str, payload_file: pathlib.Path) -> CommandResponse:
    """
    Register new Connector
    """
    service_state = state["services"]
    if not payload_file.exists():
        print(f"file {payload_file} not found in directory")
        return CommandResponse.fail()
    spec = dict()
    with open(payload_file, 'r') as f:
        spec["payload"] = env.fill_template(f.read(), state)
    service = ConnectorService(azure_token=azure_token, state=service_state, spec=spec)
    response = service.create()
    if response is None:
        return CommandResponse.fail()
    connector = response.json()
    state["services"]["api"]["connector_id"] = connector.get("id")
    env.store_state_in_local(state)
    env.store_state_in_cloud(state)
    logger.info(f"Connector '{connector.get('id')}' successfully saved in state {state.get('id')}")
    return CommandResponse.success(connector, verbose=True)
