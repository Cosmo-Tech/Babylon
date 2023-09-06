import logging
import requests

from click import command
from typing import Any, Optional
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
    github_secret = env.get_global_secret(resource="github", name="token")
    run_url = context['github_run_url']
    url = f"{run_url}/cancel"
    response = requests.post(url,
                             headers={
                                 "Accept": "application/vnd.github+json",
                                 "X-GitHub-Api-Version": "2022-11-28",
                                 "Authorization": f"Bearer {github_secret}"
                             })
    if response is None:
        return CommandResponse.fail()
    response = response.json()
    return CommandResponse.success(response, verbose=True)
