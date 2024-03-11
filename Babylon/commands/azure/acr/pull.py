import logging

from click import option
from click import command
from typing import Any, Optional
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import injectcontext
from Babylon.utils.decorators import retrieve_state
from Babylon.commands.azure.acr.services.api import AzureContainerRegistryService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@option("--image", type=str, help="Remote docker image to pull, example hello-world:latest")
@retrieve_state
def pull(state: Any, image: Optional[str] = None) -> CommandResponse:
    """
    Pulls a docker image from the ACR registry
    """
    service_state = state['services']
    service = AzureContainerRegistryService(state=service_state)
    service.pull(image_tag=image)
    return CommandResponse.success()
