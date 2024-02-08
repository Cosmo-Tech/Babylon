import logging

from typing import Any, Optional
from click import argument, command
from Babylon.commands.git_hub.runs.service.api import GitHubRunsService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@argument("workflow_name", type=QueryType())
@inject_context_with_resource({'github': ['organization', 'repository']})
def get(context: Any, workflow_name: Optional[str] = None) -> CommandResponse:
    """
    Get github workflow 
    """
    service = GitHubRunsService(state=context)
    response = service.get(workflow_name=workflow_name)
    return CommandResponse.success(response, verbose=True)
