import sys
from logging import getLogger

from typing import Optional
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")


class ScenarioService:

    def __init__(self, state: dict, azure_token: str, spec: Optional[dict] = None):
        self.spec = spec
        self.state = state
        self.azure_token = azure_token

    def get_all(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        workspace_id = self.state["api"]["workspace_id"]

        if not url:
            logger.error("API url not found")
            sys.exit(1)
        if not organization_id:
            logger.error("organization_id not found")
            sys.exit(1)
        if not workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)

        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios",
            self.azure_token,
        )
        return response

    def get(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        workspace_id = self.state["api"]["workspace_id"]
        scenario_id = self.spec["scenario_id"]

        if not url:
            logger.error("API url not found")
            sys.exit(1)
        if not organization_id:
            logger.error("organization_id not found")
            sys.exit(1)
        if not workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)

        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
        )
        return response

    def update(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        workspace_id = self.state["api"]["workspace_id"]
        # need to reconsider this line when scenario manipulation in macro commands will be clearer
        scenario_id = self.state["api"]["scenario_id"]

        if not url:
            logger.error("API url not found")
            sys.exit(1)
        if not organization_id:
            logger.error("organization_id not found")
            sys.exit(1)
        if not workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)

        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
            type="PATCH",
            data=self.spec,
        )
        return response

    def create(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        workspace_id = self.state["api"]["workspace_id"]

        if not url:
            logger.error("API url not found")
            sys.exit(1)
        if not organization_id:
            logger.error("organization_id not found")
            sys.exit(1)
        if not workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)
        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios",
            self.azure_token,
            type="POST",
            data=self.spec,
        )
        return response

    def delete(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        workspace_id = self.state["api"]["workspace_id"]
        scenario_id = self.spec["scenario_id"]

        if not url:
            logger.error("API url not found")
            sys.exit(1)
        if not organization_id:
            logger.error("organization_id not found")
            sys.exit(1)
        if not workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)
        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
            type="DELETE",
        )
        return response

    def run(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        workspace_id = self.state["api"]["workspace_id"]
        scenario_id = self.spec["scenario_id"]

        if not url:
            logger.error("API url not found")
            sys.exit(1)
        if not organization_id:
            logger.error("organization_id not found")
            sys.exit(1)
        if not workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)
        response = oauth_request(
            f"{url}/organizations/{organization_id}/workspaces/"
            f"{workspace_id}/scenarios/{scenario_id}/run",
            self.azure_token,
            type="POST",
        )
        return response
