import logging

from Babylon.utils.checkers import check_ascii
from azure.mgmt.eventhub import EventHubManagementClient
from azure.mgmt.eventhub.v2015_08_01.models import ConsumerGroupCreateOrUpdateParameters
from Babylon.utils.clients import get_azure_credentials

logger = logging.getLogger("Babylon")


class AdxConsumerService:

    def __init__(self, state: dict = None) -> None:
        self.state = state

    def get(self, name: str, event_hub_name: str) -> bool:
        logger.info(f"getting consumer {name}")
        rg = self.state["azure"]["resource_group_name"]
        subscription_id = self.state["azure"]["subscription_id"]
        org_id = self.state["api"]["organization_id"].lower()
        work_id = self.state["api"]["workspace_key"].lower()
        client = EventHubManagementClient(credential=get_azure_credentials(), subscription_id=subscription_id)
        try:
            res = client.consumer_groups.get(
                resource_group_name=rg,
                namespace_name=f"{org_id}-{work_id}",
                consumer_group_name=name.lower(),
                event_hub_name=event_hub_name.lower(),
            )
            if "id" in res.as_dict().get("id"):
                return res.as_dict()
        except Exception as exp:
            logger.debug(exp)
            return False

    def add(self, name: str, event_hub_name: str) -> bool:
        logger.info(f"adding consumer {name}")
        check_ascii(name)
        rg = self.state["azure"]["resource_group_name"]
        subscription_id = self.state["azure"]["subscription_id"]
        org_id = self.state["api"]["organization_id"].lower()
        work_id = self.state["api"]["workspace_key"].lower()
        location = self.state["azure"]["resource_location"]
        client = EventHubManagementClient(credential=get_azure_credentials(), subscription_id=subscription_id)
        try:
            res = client.consumer_groups.create_or_update(
                resource_group_name=rg,
                namespace_name=f"{org_id}-{work_id}",
                consumer_group_name=name.lower(),
                event_hub_name=event_hub_name.lower(),
                parameters=ConsumerGroupCreateOrUpdateParameters(location=location, ),
            )
            return res.as_dict()
        except Exception as exp:
            logger.warning(exp)
            return dict()

    def delete(self, name: str, event_hub_name: str) -> bool:
        logger.info(f"deleting consumer {name}")
        subscription_id = self.state["azure"]["subscription_id"]
        client = EventHubManagementClient(credential=get_azure_credentials(), subscription_id=subscription_id)
        try:
            client.consumer_groups.delete()
        except Exception as exp:
            logger.debug(exp)
            return False
        return True

    def get_all(self, event_hub_name: str) -> bool:
        logger.info(f"Reading all consumers {event_hub_name}")
        rg = self.state["azure"]["resource_group_name"]
        subscription_id = self.state["azure"]["subscription_id"]
        org_id = self.state["api"]["organization_id"].lower()
        work_id = self.state["api"]["workspace_key"].lower()
        client = EventHubManagementClient(credential=get_azure_credentials(), subscription_id=subscription_id)
        try:
            res = client.consumer_groups.list_by_event_hub(
                resource_group_name=rg,
                namespace_name=f"{org_id}-{work_id}",
                event_hub_name=event_hub_name.lower(),
            )
            result = []
            for r in res:
                item = r.as_dict()
                if item.get("name") != "$Default":
                    result.append(item.get('name'))
            return result
        except Exception as exp:
            logger.warning(exp)
            return list()
