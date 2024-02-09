import logging

from typing import Any, Optional
from click import argument, command
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.commands.azure.adx.database.service.api import AdxDatabaseService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@pass_kusto_client
@argument("name", type=QueryType(), required=False)
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
