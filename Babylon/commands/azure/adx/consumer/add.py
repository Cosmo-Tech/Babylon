import logging

from typing import Any
from click import argument, command
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.commands.azure.adx.consumer.service.api import AdxConsumerService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@argument("name", type=QueryType())
@argument("event_hub_name", type=QueryType())
@inject_context_with_resource(
    {
        "api": ["organization_id", "workspace_key"],
        "azure": ["resource_group_name", "subscription_id", "resource_location"],
    }
)
def add(context: Any, name: str, event_hub_name: str) -> CommandResponse:
    """
    Create new consumer group in EventHub
    """
    apiAdxConsumer = AdxConsumerService(state=context)
    apiAdxConsumer.add(name=name, event_hub_name=event_hub_name)
    return CommandResponse.success()
