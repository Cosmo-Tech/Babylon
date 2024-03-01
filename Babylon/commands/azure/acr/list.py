from typing import Any, Optional
from click import argument, command
from Babylon.utils.decorators import injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.commands.azure.acr.services.api import AzureContainerRegistryService


@command()
@injectcontext()
@timing_decorator
@argument("server", type=str, required=False)
@retrieve_state
def list(state: Any, server: Optional[str] = None) -> CommandResponse:
    """
    List all docker images in the specified registry
    """
    service_state = state['services']
    service = AzureContainerRegistryService(state=service_state)
    service.list(server=server)
    CommandResponse.success()
