import logging

from uuid import uuid4
from Babylon.utils.checkers import check_ascii
from azure.mgmt.kusto import KustoManagementClient
from azure.mgmt.kusto.models import EventHubDataConnection

from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")


class AdxConnectionService:

    def __init__(self, kusto_client: KustoManagementClient, state: dict = None) -> None:
        self.state = state
        self.kusto_client = kusto_client

    def create(
        self,
        database_name: str,
        connection_name: str,
        consumer_group: str,
        data_format: str,
        compression_value: str,
        table_name: str,
        mapping: str
    ):
        check_ascii(database_name)
        dataconnections_operations = self.kusto_client.data_connections

        azure_subscription = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        resource_location = self.state["azure"]["resource_location"]
        organization_id = self.state["api"]["organization_id"]
        workspace_key = self.state["api"]["workspace_key"]
        adx_cluster_name = self.state["adx"]["cluster_name"]

        eventhub_id = f"/subscriptions/{azure_subscription}/"
        eventhub_id += f"resourceGroups/{resource_group_name}/"
        eventhub_id += f"providers/Microsoft.EventHub/namespaces/{organization_id}-{workspace_key}/"
        eventhub_id += f"eventhubs/{connection_name.lower()}"

        random = str(uuid4())
        try:
            managed_id = f"/subscriptions/{azure_subscription}/resourceGroups/{resource_group_name}"
            managed_id += f"/providers/Microsoft.Kusto/clusters/{adx_cluster_name}"
            poller = dataconnections_operations.begin_create_or_update(
                resource_group_name=resource_group_name,
                cluster_name=adx_cluster_name,
                database_name=database_name,
                data_connection_name=f"{organization_id.lower()}-{random[0:3].lower()}-{connection_name.lower()}",
                parameters=EventHubDataConnection(
                    consumer_group=consumer_group,
                    location=resource_location,
                    event_hub_resource_id=eventhub_id,
                    data_format=data_format,
                    compression=compression_value,
                    table_name=table_name,
                    managed_identity_resource_id=managed_id,
                    mapping_rule_name=mapping,
                ),
            )
            poller.wait()
            if not poller.done():
                return CommandResponse.fail()
        except Exception as ex:
            logger.info(ex)
            return CommandResponse.fail()

        logger.info("Successfully created adx connection")
