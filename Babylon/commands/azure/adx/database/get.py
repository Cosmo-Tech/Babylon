import logging

from typing import Any, Optional
from click import argument, command

from Babylon.utils.environment import Environment
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.commands.azure.adx.services.database import AdxDatabaseService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_kusto_client
@argument("name", type=str, required=False)
@retrieve_state
def get(
    state: Any,
    kusto_client: KustoManagementClient,
    name: Optional[str] = None,
) -> CommandResponse:
    """
    Get database from ADX cluster
    """
    service_state = state['services']
    service = AdxDatabaseService(kusto_client=kusto_client, state=service_state)
    service.get(name=name)
    return CommandResponse.success()
