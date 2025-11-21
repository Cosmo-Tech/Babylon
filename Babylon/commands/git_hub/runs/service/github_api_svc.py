import logging

import requests

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class GitHubRunsService:
    def __init__(self, state: dict = None) -> None:
        self.state = state

    def get(self, workflow_name: str):
        github_secret = env.get_global_secret(resource="github", name="token")
        org = self.state["github"]["organization"]
        repo = self.state["github"]["repository"]
        url = f"https://api.github.com/repos/{org}/{repo}/actions/runs"
        response = requests.get(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Authorization": f"Bearer {github_secret}",
            },
        )
        if response is None:
            return CommandResponse.fail()
        response = response.json()
        responses = [{"path": i.get("path"), "url": i.get("url")} for i in response["workflow_runs"]]
        workflow_name = f"azure-static-web-apps-{workflow_name}.yml"
        for workflow in responses:
            if workflow_name in workflow.get("path"):
                run_url = workflow.get("url")
                return run_url

    def cancel(self, run_url: str):
        github_secret = env.get_global_secret(resource="github", name="token")
        url = f"{run_url}/cancel"
        response = requests.post(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Authorization": f"Bearer {github_secret}",
            },
        )
        if response is None:
            return CommandResponse.fail()
        response = response.json()
        return response
