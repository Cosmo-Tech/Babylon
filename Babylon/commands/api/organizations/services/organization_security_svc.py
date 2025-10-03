import sys

from logging import getLogger
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


class OrganizationSecurityService:

    def __init__(self, keycloak_token: str, state: dict) -> None:
        self.state = state
        self.keycloak_token = keycloak_token
        self.url = self.state["api"]["url"]
        if not self.url:
            logger.error("API url not found")
            sys.exit(1)
        self.organization_id = self.state["api"]["organization_id"]
        if not self.organization_id:
            logger.error("organization id is missing")
            sys.exit(1)

    def set_default(self, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/security/default",
            self.keycloak_token,
            type="PATCH",
            data=details,
        )
        return response

    def add(self, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/security/access",
            self.keycloak_token,
            type="POST",
            data=details,
        )
        return response

    def get(self, id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/security/access/{id}",
            self.keycloak_token,
            type="GET",
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/security",
            self.keycloak_token,
            type="GET",
        )
        return response

    def update(self, id: str, details: str):
        response = oauth_request(f"{self.url}/organizations/{self.organization_id}/security/access/{id}",
                                 self.keycloak_token,
                                 type="PATCH",
                                 data=details)
        return response

    def delete(self, id: str):
        response = oauth_request(f"{self.url}/organizations/{self.organization_id}/security/access/{id}",
                                 self.keycloak_token,
                                 type="DELETE")
        return response
