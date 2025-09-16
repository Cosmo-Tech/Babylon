import logging

from typing import Any
from click import command
from click import option
from Babylon.commands.api.connectors.services.connectors_svc import ConnectorService
from Babylon.utils.decorators import injectcontext
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_azure_token
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_azure_token("csm_api")
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@option("--connector-id", "connector_id", type=str)
@retrieve_state
def delete(
    state: Any,
    azure_token: str,
    connector_id: str,
    force_validation: bool = False,
) -> CommandResponse:
    """Delete a registered connector"""
    service_state = state["services"]
    service_state["api"]["connector.storage_id"] = (connector_id or service_state["api"]["connector.storage_id"])

    service = ConnectorService(azure_token=azure_token, state=service_state)
    logger.info(f"Deleting connector: {service_state['api']['connector.storage_id']}")
    response = service.delete(force_validation=force_validation)

    if response:
        logger.info(f'Connector {service_state["api"]["connector.storage_id"]} successfully deleted')
        if (service_state["api"]["connector.storage_id"] == state["services"]["api"]["connector.storage_id"]):
            state["services"]["api"]["connector.storage_id"] = ""
            env.store_state_in_local(state)
            if env.remote:
                env.store_state_in_cloud(state)
            logger.info(f'Connector {state["services"]["api"]["connector.storage_id"]} '
                        f'successfully removed from state {state.get("id")}')
    return CommandResponse.success()
