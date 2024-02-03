import logging

from typing import Optional
from click import Choice, argument, command, option
from Babylon.commands.azure.adx.connections.service.api import AdxConnectionService
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from azure.mgmt.kusto import KustoManagementClient
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.clients import pass_kusto_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
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
@inject_context_with_resource(
    {
        "api": ["organization_id", "workspace_key"],
        "azure": ["resource_group_name", "resource_location", "subscription_id"],
        "adx": ["cluster_name"],
    }
)
def create(
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
    apiAdxConn = AdxConnectionService(kusto_client=kusto_client)
    apiAdxConn.create(
        compression_value=compression_value,
        connection_name=connection_name,
        consumer_group=consumer_group,
        database_name=database_name,
        data_format=data_format,
        table_name=table_name,
        mapping=mapping,
    )
    return CommandResponse.success()
