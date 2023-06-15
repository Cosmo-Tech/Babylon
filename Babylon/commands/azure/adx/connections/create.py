import logging
from typing import Optional

from click import argument, command, option
from azure.mgmt.kusto import KustoManagementClient
from azure.mgmt.kusto.models import EventHubDataConnection
from azure.mgmt.kusto.models import EventHubDataFormat

from Babylon.utils.typing import QueryType

from .....utils.clients import pass_kusto_client
from .....utils.environment import Environment
from .....utils.response import CommandResponse
from .....utils.decorators import require_deployment_key
from .....utils.decorators import require_platform_key
from .....utils.decorators import timing_decorator

from datetime import timedelta

logger = logging.getLogger("Babylon")


@command()
@pass_kusto_client
@require_deployment_key('organization_id')
@require_deployment_key('workspace_key')
@require_deployment_key("resource_group_name")
@require_deployment_key("workspace_key")
@require_deployment_key('resources_location')
@require_platform_key('azure_subscription')
@require_platform_key('adx_cluster_name')
@timing_decorator
@argument("connection_name", type=QueryType())
@argument("data_format", type=QueryType())
@argument("database_name", type=QueryType(), default="%deploy%adx_database_name")
@option("-tn", "--table-name", "table_name", type=QueryType(), default=None)
def create(kusto_client: KustoManagementClient,
           azure_subscription: str,
           organization_id: str,
           resource_group_name: str,
           workspace_key: str,
           connection_name: str,
           data_format: str,
           resources_location: str,
           adx_cluster_name: str,
           table_name: Optional[str] = None,
           database_name: Optional[str] = None) -> CommandResponse:
    """Create database in ADX cluster"""

    dataconnections_operations = kusto_client.data_connections
    eventhub_id = f"/subscriptions/{azure_subscription}/"
    eventhub_id += f"resourceGroups/{resource_group_name}/"
    eventhub_id += f"providers/Microsoft.EventHub/namespaces/{organization_id}-{workspace_key}/"
    eventhub_id += f"eventhubs/{connection_name.lower()}"

    try:
        poller = dataconnections_operations.begin_create_or_update(
                resource_group_name=resource_group_name,
                cluster_name=adx_cluster_name,
                database_name=database_name,
                data_connection_name=f"{organization_id.lower()}-{connection_name.lower()}",
                parameters=EventHubDataConnection(
                    consumer_group="$Default",
                    location=resources_location,
                    event_hub_resource_id=eventhub_id,
                    data_format=data_format,
                    table_name=table_name
                )
            )
        poller.wait()
        # check if done
        if not poller.done():
            return CommandResponse.fail()
    except Exception as ex:
        logger.info(ex)
        return CommandResponse.fail()
    
    return CommandResponse.success()
