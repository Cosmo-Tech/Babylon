import logging

from click import option
from click import command
from typing import Any, Optional
from Babylon.utils.decorators import injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.commands.azure.acr.service.api import AzureContainerRegistryService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@option("--image", type=str, help="Remote docker image to pull, example hello-world:latest")
@retrieve_state
def delete(state: Any, image: Optional[str] = None) -> CommandResponse:
    """
    Delete docker image from selected repository
    """
    service_state = state['services']
    service = AzureContainerRegistryService(state=service_state)
    service.delete(image_tag=image)
    return CommandResponse.success()
