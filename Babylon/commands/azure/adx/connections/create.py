import logging

from typing import Any, Optional
from click import Choice, argument, command, option
from azure.mgmt.kusto import KustoManagementClient
from azure.mgmt.kusto.models import EventHubDataConnection
from Babylon.utils.checkers import check_ascii
from Babylon.utils.typing import QueryType
from Babylon.utils.clients import pass_kusto_client
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import inject_context_with_resource
from uuid import uuid4

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@timing_decorator
@pass_kusto_client
@option("--mapping", "mapping", type=QueryType())
@option("--compression", "compression_value", type=Choice(['None', "GZip"]), default="None")
@option("--consumer-group", "consumer_group", type=QueryType(), default="$Default")
@option("--table-name", "table_name", type=QueryType())
@option("--data-format", "data_format", type=Choice(["JSON", "CSV", "TXT"]), required=True)
@argument("connection_name", type=QueryType())
@argument("database_name", type=QueryType())
@inject_context_with_resource({
    'api': ['organization_id', 'workspace_key'],
    'azure': ['resource_group_name', 'resource_location', 'subscription_id'],
    'adx': ['cluster_name']
})
def create(context: Any, kusto_client: KustoManagementClient, connection_name: str, data_format: str,
           compression_value: str, consumer_group: str, mapping: str, table_name: Optional[str],
           database_name: Optional[str]) -> CommandResponse:
    """
    Create new connection in ADX database
    """
    check_ascii(database_name)
    dataconnections_operations = kusto_client.data_connections

    azure_subscription = context['azure_subscription_id']
    resource_group_name = context['azure_resource_group_name']
    resource_location = context['azure_resource_location']
    organization_id = context['api_organization_id']
    workspace_key = context['api_workspace_key']
    adx_cluster_name = context['adx_cluster_name']

    eventhub_id = f"/subscriptions/{azure_subscription}/"
    eventhub_id += f"resourceGroups/{resource_group_name}/"
    eventhub_id += f"providers/Microsoft.EventHub/namespaces/{organization_id}-{workspace_key}/"
    eventhub_id += f"eventhubs/{connection_name.lower()}"

    random = str(uuid4())
    try:
        poller = dataconnections_operations.begin_create_or_update(
            resource_group_name=resource_group_name,
            cluster_name=adx_cluster_name,
            database_name=database_name,
            data_connection_name=f"{organization_id.lower()}-{random[0:3].lower()}-{connection_name.lower()}",
            parameters=EventHubDataConnection(consumer_group=consumer_group,
                                              location=resource_location,
                                              event_hub_resource_id=eventhub_id,
                                              data_format=data_format,
                                              compression=compression_value,
                                              table_name=table_name,
                                              mapping_rule_name=mapping))
        poller.wait()
        if not poller.done():
            return CommandResponse.fail()
    except Exception as ex:
        logger.info(ex)
        return CommandResponse.fail()

    logger.info("Successfully created adx connection")
    return CommandResponse.success()
