import logging

from click import option
from click import command
from typing import Any, Optional
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import retrieve_state, wrapcontext
from Babylon.commands.azure.acr.service.api import AzureContainerRegistryService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@option("--image", type=QueryType(), help="Local docker image to push")
@retrieve_state
def push(
    state: Any,
    image: Optional[str],
) -> CommandResponse:
    """
    Push a docker image to the ACR registry
    """
    service = AzureContainerRegistryService(state=state)
    service.push(image_tag=image)
    return CommandResponse.success()
