import logging
from Babylon.utils.checkers import check_ascii
from azure.mgmt.eventhub import EventHubManagementClient
from azure.mgmt.eventhub.v2015_08_01.models import ConsumerGroupCreateOrUpdateParameters
from Babylon.utils.clients import get_azure_credentials

logger = logging.getLogger("Babylon")


class AdxConsumerService:

    def __init__(self, state: dict = None) -> None:
        self.state = state

    def add(self, name: str, event_hub_name: str):
        check_ascii(name)
        rg = self.state["azure"]["resource_group_name"]
        subscription_id = self.state["azure"]["subscription_id"]
        org_id = self.state["api"]["organization_id"].lower()
        work_id = self.state["api"]["workspace_key"].lower()
        location = self.state["azure"]["resource_location"]
        client = EventHubManagementClient(
            credential=get_azure_credentials(), subscription_id=subscription_id
        )
        client.consumer_groups.create_or_update(
            resource_group_name=rg,
            namespace_name=f"{org_id}-{work_id}",
            consumer_group_name=name.lower(),
            event_hub_name=event_hub_name.lower(),
            parameters=ConsumerGroupCreateOrUpdateParameters(
                location=location,
            ),
        )
