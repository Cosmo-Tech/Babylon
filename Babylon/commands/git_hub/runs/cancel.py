import logging

from click import command
from typing import Any, Optional
from Babylon.commands.git_hub.runs.service.api import GitHubRunsService
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@inject_context_with_resource({'github': ['run_url']})
def cancel(context: Any, workflow_name: Optional[str] = None) -> CommandResponse:
    """
    Cancel a github workflow from run url
    """
    api_runs_github = GitHubRunsService(state=context)
    response = api_runs_github.cancel()
    return CommandResponse.success(response, verbose=True)
