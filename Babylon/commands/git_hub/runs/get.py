import logging

from typing import Any, Optional
from click import argument, command
from Babylon.commands.git_hub.runs.service.api import GitHubRunsService
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
<<<<<<< HEAD
@argument("workflow_name", type=str)
=======
@argument("workflow_name", type=QueryType())
>>>>>>> 53b0a6f8 (add injectcontext)
@retrieve_state
def get(state: Any, workflow_name: Optional[str] = None) -> CommandResponse:
    """
    Get github workflow 
    """
    service_state = state['services']
    service = GitHubRunsService(state=service_state)
    response = service.get(workflow_name=workflow_name)
    return CommandResponse.success(response, verbose=True)
