import logging

from typing import Any, Optional
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_kusto_client
from click import Choice, argument, command, option
from Babylon.utils.decorators import retrieve_state, timing_decorator, injectcontext
from Babylon.commands.azure.adx.services.connection import AdxConnectionService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_kusto_client
@option("--mapping", "mapping", type=QueryType(), help="ADX mapping name")
@option(
    "--compression",
    "compression_value",
    type=Choice(["None", "GZip"]),
    default="None",
    help="Compression Gzip or None",
)
@option(
    "--consumer-group",
    "consumer_group",
    type=QueryType(),
    default="$Default",
    help="Consumer group name",
)
@option("--table-name", "table_name", type=QueryType(), help="ADX table name")
@option(
    "--data-format",
    "data_format",
    type=Choice(["JSON", "CSV", "TXT"]),
    required=True,
    help="Data format",
)
@argument("connection_name", type=QueryType())
@argument("database_name", type=QueryType())
@retrieve_state
def create(
    state: Any,
    kusto_client: KustoManagementClient,
    connection_name: str,
    data_format: str,
    compression_value: str,
    consumer_group: str,
    mapping: str,
    table_name: Optional[str],
    database_name: Optional[str],
) -> CommandResponse:
    """
    Create new connection in ADX database
    """
    service_state = state['services']
    service = AdxConnectionService(kusto_client=kusto_client, state=service_state)
    service.create(
        compression_value=compression_value,
        connection_name=connection_name,
        consumer_group=consumer_group,
        database_name=database_name,
        data_format=data_format,
        table_name=table_name,
        mapping=mapping,
    )
    return CommandResponse.success()
