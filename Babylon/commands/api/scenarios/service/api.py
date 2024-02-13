import sys
from logging import getLogger

from typing import Optional

from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")


class ScenarioService:

    def __init__(self, state: dict, azure_token: str, spec: Optional[dict] = None):
        self.spec = spec
        self.state = state
        self.url = state["api"]["url"]
        self.organization_id = state["api"]["organization_id"]
        self.workspace_id = state["api"]["workspace_id"]
        self.azure_token = azure_token

        if not self.url:
            logger.error("API url not found")
            sys.exit(1)
        if not self.organization_id:
            logger.error("organization_id not found")
            sys.exit(1)
        if not self.workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios",
            self.azure_token,
        )
        return response

    def get(self):
        scenario_id = self.state["api"]["scenario_id"]

        if not scenario_id:
            logger.error("scenario_id is missing")
            sys.exit(1)

        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
        )
        return response

    def update(self):
        scenario_id = self.state["api"]["scenario_id"]

        if not scenario_id:
            logger.error("scenario_id is missing")
            sys.exit(1)

        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
            type="PATCH",
            data=details,
        )
        return response

    def create(self):
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios",
            self.azure_token,
            type="POST",
            data=details,
        )
        return response

    def delete(self, force_validation: bool):
        scenario_id = self.state["api"]["scenario_id"]

        if not scenario_id:
            logger.error("scenario_id is missing")
            sys.exit(1)

        if not force_validation and not confirm_deletion("solution", scenario_id):
            return None

        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
            type="DELETE",
        )
        return response

    def run(self):
        scenario_id = self.state["api"]["scenario_id"]

        if not scenario_id:
            logger.error("scenario_id is missing")
            sys.exit(1)

        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{scenario_id}/run",
            self.azure_token,
            type="POST",
        )
        return response
