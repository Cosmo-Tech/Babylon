import logging
from Babylon.utils.checkers import check_ascii
from azure.mgmt.eventhub import EventHubManagementClient
from azure.mgmt.eventhub.v2015_08_01.models import ConsumerGroupCreateOrUpdateParameters
from Babylon.utils.clients import get_azure_credentials

logger = logging.getLogger("Babylon")


class AdxConsumerService:

    def add(self, name: str, context: dict, event_hub_name: str):
        check_ascii(name)
        rg = context["azure_resource_group_name"]
        subscription_id = context["azure_subscription_id"]
        org_id = context["api_organization_id"].lower()
        work_id = context["api_workspace_key"].lower()
        location = context["azure_resource_location"]

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
