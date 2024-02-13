import sys
from logging import getLogger
from typing import Optional

from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")


class ScenarioRunService:

    def __init__(self, azure_token: str, state: dict, spec: Optional[dict] = None):
        self.state = state
        self.spec = spec
        self.azure_token = azure_token
        self.url = self.state["api"]["url"]
        self.organization_id = self.state["api"]["organization_id"]
        self.scenariorun_id = self.state["api"]["scenariorun_id"]
        if not self.organization_id:
            logger.error("organization id is missing")
            sys.exit(1)
        if not self.scenariorun_id:
            logger.error("solution id is missing")
            sys.exit(1)

    def logs(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/scenarioruns/{self.scenariorun_id}/logs",
            self.azure_token)
        return response

    def cumulated_logs(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/scenarioruns/{self.scenariorun_id}/cumulatedlogs",
            self.azure_token)
        return response

    def status(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/scenarioruns/{self.scenariorun_id}/status",
            self.azure_token)
        return response

    def stop(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/scenarioruns/{self.scenariorun_id}/stop",
            self.azure_token, "POST")
        return response
