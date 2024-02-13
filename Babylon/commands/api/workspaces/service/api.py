import json
import sys

from logging import getLogger
from typing import Optional
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


class WorkspaceService:

    def __init__(self, state: dict, azure_token: str, spec: Optional[dict] = None):
        self.spec = spec
        self.state = state
        self.azure_token = azure_token
        self.url = state["api"]["url"]
        if not self.url:
            logger.error("API url not found")
            sys.exit(1)
        self.organization_id = state["api"]["organization_id"]
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
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces",
            self.azure_token,
            type="POST",
            data=details,
        )
        return response

    def update(self):
        workspace_id = self.state["api"]["workspace_id"]
        details = self.spec["payload"]
        if not workspace_id:
            logger.error("workspace id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{workspace_id}",
            self.azure_token,
            type="PATCH",
            data=details,
        )
        return response

    def delete(self):
        workspace_id = self.state["api"]["workspace_id"]
        if not workspace_id:
            logger.error("workspace id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{workspace_id}",
            self.azure_token,
            type="DELETE",
        )
        return response

    def send_key(self):
        secret_eventhub = env.get_project_secret(
            organization_id=self.organization_id,
            workspace_key=self.state["api"]["workspace_key"],
            name="eventhub",
        )
        if not secret_eventhub:
            logger.error("workspace secret key is missing in vault")
            sys.exit(1)
        details_json = {"dedicatedEventHubKey": secret_eventhub.replace('"', "")}
        details_json = json.dumps(details_json, indent=4, default=str)
        work_id = self.state["api"]["workspace_id"]
        workspace_id = self.state["api"]["workspace_id"]
        if not workspace_id:
            logger.error("workspace id not found")
            sys.exit(1)
        response = oauth_request(
            f'{self.url}/organizations/{self.organization_id}/workspaces/{work_id}/secret',
            self.azure_token,
            type="POST",
            data=details_json,
        )
        return response
