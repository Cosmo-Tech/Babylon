import sys
from logging import getLogger

from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")


class RunService:

    def __init__(self, keycloak_token: str, state: dict):
        self.state = state
        self.keycloak_token = keycloak_token
        self.url = self.state["api"]["url"]
        self.organization_id = self.state["api"]["organization_id"]
        self.run_id = self.state["api"]["run_id"]
        if not self.organization_id:
            logger.error("organization id is missing")
            sys.exit(1)
        if not self.run_id:
            logger.error("solution id is missing")
            sys.exit(1)

    def logs(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/runs/{self.run_id}/logs",
            self.keycloak_token)
        return response

    def status(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/runs/{self.run_id}/status",
            self.keycloak_token)
        return response

    def stop(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/runs/{self.run_id}/stop",
            self.keycloak_token, "POST")
        return response
