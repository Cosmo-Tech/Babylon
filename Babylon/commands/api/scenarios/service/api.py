from typing import Optional
from Babylon.utils.request import oauth_request


class ScenarioService:

    def __init__(self, state: dict, azure_token: str, spec: Optional[dict] = None):
        self.spec = spec
        self.state = state
        self.azure_token = azure_token

    def get_all(self):
        url = self.state["state"]["api"]["url"]
        organization_id = self.state["state"]["api"]["organization_id"]
        workspace_id = self.state["state"]["api"]["workspace_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios",
            self.azure_token,
        )
        return response

    def get(self):
        url = self.state["state"]["api"]["url"]
        organization_id = self.state["state"]["api"]["organization_id"]
        workspace_id = self.state["state"]["api"]["workspace_id"]
        scenario_id = self.state["state"]["api"]["scenario_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
        )
        return response

    def update(self):
        url = self.state["state"]["api"]["url"]
        organization_id = self.state["state"]["api"]["organization_id"]
        workspace_id = self.state["state"]["api"]["workspace_id"]
        scenario_id = self.state["state"]["api"]["scenario_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
            type="PATCH",
            data=self.spec,
        )
        return response

    def create(self):
        url = self.state["state"]["api"]["url"]
        organization_id = self.state["state"]["api"]["organization_id"]
        workspace_id = self.state["state"]["api"]["workspace_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios",
            self.azure_token,
            type="POST",
            data=self.spec,
        )
        return response

    def delete(self):
        url = self.state["state"]["api"]["url"]
        organization_id = self.state["state"]["api"]["organization_id"]
        workspace_id = self.state["state"]["api"]["workspace_id"]
        scenario_id = self.state["state"]["api"]["scenario_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
            type="DELETE",
        )
        return response

    def run(self):
        url = self.state["state"]["api"]["url"]
        organization_id = self.state["state"]["api"]["organization_id"]
        workspace_id = self.state["state"]["api"]["workspace_id"]
        scenario_id = self.state["state"]["api"]["scenario_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios/{scenario_id}/run",
            self.azure_token,
            type="POST",
        )
        return response
