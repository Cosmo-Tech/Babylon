import logging

from click import option
from click import command
from typing import Any, Optional
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import timing_decorator
from Babylon.commands.azure.acr.service.api import AzureContainerRegistryService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
@option("--image", type=QueryType(), help="Remote docker image to pull, example hello-world:latest")
@option("-D", "force_validation", is_flag=True, default=True, help="Force Delete")
@inject_context_with_resource({'acr': ['login_server', 'simulator_repository', 'simulator_version']}, required=False)
def delete(context: Any, image: Optional[str] = None, force_validation: Optional[bool] = False) -> CommandResponse:
    """
    Delete docker image from selected repository
    """
    state = dict()
    state['acr'] = dict()
    state['acr']['login_server'] = context['acr_login_server']
    state['acr']['simulator_repository'] = context['acr_simulator_repository']
    state['acr']['simulator_version'] = context['acr_simulator_version']
    service = AzureContainerRegistryService(state=state)
    service.delete(state, image_tag=image)
    return CommandResponse.success()
