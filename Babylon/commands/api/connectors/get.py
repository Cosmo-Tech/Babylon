from logging import getLogger
from typing import Any
from click import option
from click import command
from Babylon.commands.api.connectors.services.connectors_svc import ConnectorService
from Babylon.utils.decorators import injectcontext
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import output_to_file

logger = getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@output_to_file
@pass_azure_token("csm_api")
@option("--connector-id", "connector_id", type=str)
@retrieve_state
def get(state: Any, azure_token: str, connector_id: str) -> CommandResponse:
    """Get a registered connector details"""
    service_state = state["services"]
    service_state["api"]["connector.storage_id"] = (connector_id or service_state["api"]["connector.storage_id"])
    logger.info(f"Searching connector: {service_state['api']['connector.storage_id']}")
    service = ConnectorService(azure_token=azure_token, state=service_state)
    response = service.get()
    if response is None:
        return CommandResponse.fail()
    connector = response.json()
    return CommandResponse.success(connector, verbose=True)
