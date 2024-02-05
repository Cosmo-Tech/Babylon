from Babylon.utils.request import oauth_request


class ScenarioRunService:
    def __init__(self, state: dict, spec: dict, azure_token: str):
        self.state = state
        self.spec = spec
        self.azure_token = azure_token

    def logs(self):
        return oauth_request(
            f"{self.state['api']['url']}/organizations/{self.state['api']['organization_id']}/scenarioruns/{self.state['api']['scenariorun_id']}/logs",
            self.azure_token)

    def cumulatedlogs(self):
        return oauth_request(
            f"{self.state['api']['url']}/organizations/{self.state['api']['organization_id']}/scenarioruns/{self.state['api']['scenariorun_id']}/cumulatedlogs",
            self.azure_token)

    def status(self):
        return oauth_request(
            f"{self.state['api']['url']}/organizations/{self.state['api']['organization_id']}/scenarioruns/{self.state['api']['scenariorun_id']}/status",
            self.azure_token)

    def stop(self):
        return oauth_request(
            f"{self.state['api']['url']}/organizations/{self.state['api']['organization_id']}/scenarioruns/{self.state['api']['scenariorun_id']}/stop",
            self.azure_token)
