import sys
from logging import getLogger

from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")


class ScenarioSecurityService:

    def __init__(self, azure_token: str, state: dict) -> None:
        self.state = state
        self.azure_token = azure_token
        self.url = self.state["api"]["url"]
        if not self.url:
            logger.error("API url not found")
            sys.exit(1)
        self.organization_id = self.state["api"]["organization_id"]
        if not self.organization_id:
            logger.error("organization id is missing")
            sys.exit(1)
        self.workspace_id = self.state["api"]["workspace_id"]
        if not self.workspace_id:
            logger.error("workspace id is missing")
            sys.exit(1)
        self.scenario_id = self.state["api"]["scenario_id"]
        if not self.scenario_id:
            logger.error("scenario id is missing")
            sys.exit(1)

    def get(self, id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{self.scenario_id}/security/access/{id}",
            self.azure_token,
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{self.scenario_id}/security",
            self.azure_token,
        )
        return response

    def add(self, details: dict):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{self.scenario_id}/security/access",
            self.azure_token,
            type="POST",
            data=details,
        )
        return response

    def update(self, details: dict, id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{self.scenario_id}/security/access/{id}",
            self.azure_token,
            type="POST",
            data=details,
        )
        return response

    def delete(self, id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{self.scenario_id}/security/access/{id}",
            self.azure_token,
            type="DELETE",
        )
        return response

    def set_default(self, details: dict):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{self.scenario_id}/security/default",
            self.azure_token,
            type="POST",
            data=details,
        )
        return response
