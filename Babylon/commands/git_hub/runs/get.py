import logging
import requests

from typing import Any, Optional
from click import argument, command
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.environment import Environment
from Babylon.utils.messages import SUCCESS_CONFIG_UPDATED
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
    github_secret = env.get_global_secret(resource="github", name="token")
    org = context["github_organization"] or env.configuration.get_var(resource_id="github", var_name="organization")
    repo = context["github_repository"] or env.configuration.get_var(resource_id="github", var_name="repository")
    url = f"https://api.github.com/repos/{org}/{repo}/actions/runs"
    response = requests.get(url,
                            headers={
                                "Accept": "application/vnd.github+json",
                                "X-GitHub-Api-Version": "2022-11-28",
                                "Authorization": f"Bearer {github_secret}"
                            })
    if response is None:
        return CommandResponse.fail()
    response = response.json()
    responses = [{"path": i.get("path"), "url": i.get("url")} for i in response['workflow_runs']]
    workflow_name = f"azure-static-web-apps-{workflow_name}.yml"
    for workflow in responses:
        if workflow_name in workflow.get("path"):
            run_url = workflow.get("url")
            env.configuration.set_var(resource_id="github", var_name="run_url", var_value=run_url)
            logger.info(SUCCESS_CONFIG_UPDATED("github", "run_url"))
            env.configuration.set_var(resource_id="github",
                                    var_name="workflow_path",
                                    var_value=workflow.get("path"))
            logger.info(SUCCESS_CONFIG_UPDATED("github", "workflow_path"))
    return CommandResponse.success()
