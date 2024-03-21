import logging

from click import option
from click import command
from typing import Any, Optional
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import retrieve_state
from Babylon.utils.decorators import injectcontext
from Babylon.commands.azure.acr.services.acr_api_svc import AzureContainerRegistryService

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@option("--image", type=str, help="Local docker image to push")
@retrieve_state
def push(
    state: Any,
    image: Optional[str],
) -> CommandResponse:
    """
    Push a docker image to the ACR registry
    """
    service_state = state['services']
    service = AzureContainerRegistryService(state=service_state)
    service.push(image_tag=image)
    return CommandResponse.success()
