import logging

from typing import Any
from click import argument, command

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.commands.azure.adx.services.consumer import AdxConsumerService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
<<<<<<< HEAD
<<<<<<< HEAD
@argument("name", type=str)
@argument("event_hub_name", type=str)
=======
@argument("name", type=QueryType())
@argument("event_hub_name", type=QueryType())
>>>>>>> 53b0a6f8 (add injectcontext)
=======
@argument("name", type=str)
@argument("event_hub_name", type=str)
>>>>>>> cb4637b4 (remove querytype)
@retrieve_state
def add(state: Any, name: str, event_hub_name: str) -> CommandResponse:
    """
    Create new consumer group in EventHub
    """
    service_state = state['services']
    service = AdxConsumerService(state=service_state)
    service.add(name=name, event_hub_name=event_hub_name)
    return CommandResponse.success()
