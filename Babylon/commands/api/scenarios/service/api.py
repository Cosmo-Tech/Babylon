from typing import Optional
from Babylon.utils.request import oauth_request


class ScenarioService:

    def __init__(self, state: dict, spec: Optional = None):
        self.spec = spec
        self.state = state

    def get_all(self):
        return oauth_request(
            f"{self.state['api_url']}/organizations/{self.state['organizationId']}/workspaces/"
            f"{self.state['workspaceId']}/scenarios",
            self.state["azure_token"],
        )

    def get(self):
        return oauth_request(
            f"{self.state['api_url']}/organizations/{self.state['organizationId']}/workspaces/"
            f"{self.state['workspaceId']}/scenarios/{self.state['scenario_id']}",
            self.state["azure_token"],
        )

    def update(self):
        return oauth_request(
            f"{self.state['api_url']}/organizations/{self.state['organizationId']}/workspaces/"
            f"{self.state['workspaceId']}/scenarios/{self.state['scenario_id']}",
            self.state["azure_token"],
            type="PATCH",
            data=self.spec,
        )

    def create(self):
        return oauth_request(
            f"{self.state['api_url']}/organizations/{self.state['organizationId']}/workspaces/"
            f"{self.state['workspaceId']}/scenarios",
            self.state["azure_token"],
            type="POST",
            data=self.spec,
        )

    def delete(self):
        return oauth_request(
            f"{self.state['api_url']}/organizations/{self.state['organizationId']}/workspaces/"
            f"{self.state['workspaceId']}/scenarios/{self.state['scenario_id']}",
            self.state["azure_token"],
            type="DELETE",
        )

    def run(self):
        return oauth_request(
            f"{self.state['api_url']}/organizations/{self.state['organizationId']}/workspaces/"
            f"{self.state['workspaceId']}/scenarios/{self.state['scenario_id']}/run",
            self.state["azure_token"],
            type="POST",
        )
