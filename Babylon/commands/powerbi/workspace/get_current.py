import logging

from typing import Any
from click import command
from Babylon.commands.powerbi.workspace.service.api import AzurePowerBIWorkspaceService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.credentials import pass_powerbi_token

logger = logging.getLogger("Babylon")


@command()
@wrapcontext()
@pass_powerbi_token()
@inject_context_with_resource({"powerbi": ["workspace"]})
def get_current(
    context: Any,
    powerbi_token: str,
) -> CommandResponse:
    """
    Get a specific workspace information
    """
    service = AzurePowerBIWorkspaceService(
        powerbi_token=powerbi_token, state=context
    )
    response = service.get_current()
    return CommandResponse(data=response, verbose=True)
