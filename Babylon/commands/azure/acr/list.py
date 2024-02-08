from typing import Any, Optional
from click import argument, command
from Babylon.utils.typing import QueryType
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import retrieve_state, timing_decorator
from Babylon.commands.azure.acr.service.api import AzureContainerRegistryService


@command()
@wrapcontext()
@timing_decorator
@argument("server", type=QueryType(), required=False)
@retrieve_state
def list(state: Any, server: Optional[str] = None) -> CommandResponse:
    """
    List all docker images in the specified registry
    """
    service = AzureContainerRegistryService(state=state)
    service.list(server=server)
    CommandResponse.success()
