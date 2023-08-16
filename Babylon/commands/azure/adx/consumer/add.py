import logging

from typing import Any
from azure.identity import DefaultAzureCredential
from click import argument, command
from azure.mgmt.eventhub import EventHubManagementClient
from azure.mgmt.eventhub.v2015_08_01.models import ConsumerGroupCreateOrUpdateParameters
from Babylon.utils.checkers import check_ascii
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.response import CommandResponse
from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS_CREATED

from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@argument("name", type=QueryType())
@argument("event_hub_name", type=QueryType())
@inject_context_with_resource({
    'api': ['organization_id', 'workspace_key'],
    'azure': ['resource_group_name', "subscription_id", "resource_location"]
})
def add(context: Any, name: str, event_hub_name: str) -> CommandResponse:
    """
    Create new consumer group in EventHub
    """
    check_ascii(name)
    azure_subscription = context['azure_subscription_id']
    rg = context['azure_resource_group_name']
    org_id = context['api_organization_id'].lower()
    work_id = context['api_workspace_key'].lower()
    location = context['azure_resource_location']

    client = EventHubManagementClient(credential=DefaultAzureCredential(), subscription_id=azure_subscription)
    client.consumer_groups.create_or_update(resource_group_name=rg,
                                            namespace_name=f"{org_id}-{work_id}",
                                            consumer_group_name=name.lower(),
                                            event_hub_name=event_hub_name.lower(),
                                            parameters=ConsumerGroupCreateOrUpdateParameters(location=location, ))
    logger.info(SUCCESS_CREATED("consumer adx", f"{org_id}-{work_id}/{event_hub_name.lower()}"))
    return CommandResponse.success()
