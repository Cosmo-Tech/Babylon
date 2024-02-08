from typing import Optional

from Babylon.utils.request import oauth_request


class ScenarioRunService:
    def __init__(self, state: dict, azure_token: str, spec: Optional[dict]=None):
        self.state = state
        self.spec = spec
        self.azure_token = azure_token

    def logs(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        scenariorun_id = self.state["api"]["scenariorun_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/scenarioruns/{scenariorun_id}/logs", self.azure_token)
        return response

    def cumulated_logs(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        scenariorun_id = self.state["api"]["scenariorun_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/scenarioruns/{scenariorun_id}/cumulatedlogs", self.azure_token)
        return response

    def status(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        scenariorun_id = self.state["api"]["scenariorun_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/scenarioruns/{scenariorun_id}/status", self.azure_token)
        return response

    def stop(self):
        url = self.state["api"]["url"]
        organization_id = self.state["api"]["organization_id"]
        scenariorun_id = self.state["api"]["scenariorun_id"]
        response = oauth_request(
            f"{url}/organizations/{organization_id}/scenarioruns/{scenariorun_id}/stop", self.azure_token, "POST")
        return response
