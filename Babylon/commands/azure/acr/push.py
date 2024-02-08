import logging

from typing import Any, Optional
from click import command
from click import option
from Babylon.commands.azure.acr.service.api import AzureContainerRegistryService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@option("--image", type=QueryType(), help="Local docker image to push")
@inject_context_with_resource({'acr': ['login_server', 'simulator_repository', 'simulator_version']}, required=False)
def push(
    context: Any,
    image: Optional[str],
) -> CommandResponse:
    """
    Push a docker image to the ACR registry
    """
    state = dict()
    state['acr'] = dict()
    state['acr']['login_server'] = context['acr_login_server']
    state['acr']['simulator_repository'] = context['acr_simulator_repository']
    state['acr']['simulator_version'] = context['acr_simulator_version']
    service = AzureContainerRegistryService(state=state)
    service.push(image_tag=image)
    return CommandResponse.success()
