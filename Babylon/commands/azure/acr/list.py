from typing import Any, Optional
from click import argument, command
from Babylon.utils.typing import QueryType
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.commands.azure.acr.service.api import AzureContainerRegistryService


@command()
@wrapcontext()
@timing_decorator
@argument("server", type=QueryType(), required=False)
@inject_context_with_resource({'acr': ['login_server']})
def list(context: Any, server: Optional[str] = None) -> CommandResponse:
    """
    List all docker images in the specified registry
    """
    state = dict()
    state['acr'] = dict()
    state['acr']['login_server'] = context['acr_login_server']
    acrApi = AzureContainerRegistryService(state=state)
    acrApi.list()
    CommandResponse.success()
