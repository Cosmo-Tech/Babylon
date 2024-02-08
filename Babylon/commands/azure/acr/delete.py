import logging

from click import option
from click import command
from typing import Any, Optional
from Babylon.utils.typing import QueryType
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.commands.azure.acr.service.api import AzureContainerRegistryService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@option("--image", type=QueryType(), help="Remote docker image to pull, example hello-world:latest")
@retrieve_state
def delete(state: Any, image: Optional[str] = None) -> CommandResponse:
    """
    Delete docker image from selected repository
    """
    service = AzureContainerRegistryService(state=state)
    service.delete(state, image_tag=image)
    return CommandResponse.success()
