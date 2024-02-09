import logging

from typing import Any
from click import command
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.commands.git_hub.runs.service.api import GitHubRunsService
from Babylon.utils.decorators import retrieve_state, wrapcontext

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@retrieve_state
def cancel(state: Any) -> CommandResponse:
    """
    Cancel a github workflow from run url
    """
    service_state = state['services']
    service = GitHubRunsService(state=service_state)
    response = service.cancel()
    return CommandResponse.success(response, verbose=True)
