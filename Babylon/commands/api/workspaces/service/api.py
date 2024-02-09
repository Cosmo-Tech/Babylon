import sys
from logging import getLogger
from typing import Optional

from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")


class WorkspaceService:

    def __init__(self, state: dict, azure_token: str, spec: Optional[dict] = None):
        self.spec = spec
        self.state = state
        self.azure_token = azure_token
        self.url = state["api"]["url"]
        self.organization_id = state["api"]["organization_id"]

        if not self.url:
            logger.error("API url not found")
            sys.exit(1)
        if not self.organization_id:
            logger.error("organization_id not found")
            sys.exit(1)

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces",
            self.azure_token,
        )
        return response

    def get(self):
        workspace_id = self.state["api"]["workspace_id"]
        if not workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{workspace_id}",
            self.azure_token,
        )
        return response

    def create(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces",
            self.azure_token,
            type="POST",
            data=self.spec,
        )
        return response

    def update(self):
        workspace_id = self.state["api"]["workspace_id"]
        if not workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{workspace_id}",
            self.azure_token,
            type="PATCH",
            data=self.spec,
        )
        return response

    def delete(self):
        workspace_id = self.state["api"]["workspace_id"]
        if not workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{workspace_id}",
            self.azure_token,
            type="DELETE",
        )
        return response
