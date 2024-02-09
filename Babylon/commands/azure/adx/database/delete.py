import logging

from typing import Any, Optional
from Babylon.utils.typing import QueryType
from click import argument, command, option
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
@option(
    "--current",
    "current",
    type=QueryType(),
    is_flag=True,
    help="Delete database adx referenced in configuration",
)
@argument("name", type=QueryType())
@retrieve_state
def delete(
    state: Any,
    kusto_client: KustoManagementClient,
    name: Optional[str] = None,
    current: bool = False,
) -> CommandResponse:
    """
    Delete database in ADX cluster
    """
    service_state = state['services']
    service = AdxDatabaseService(kusto_client=kusto_client, state=service_state)
    service.delete(
        name=name,
        current=current,
    )
    return CommandResponse.success()
