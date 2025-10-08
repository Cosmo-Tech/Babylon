import sys

from logging import getLogger
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


class SolutionSecurityService:

    def __init__(self, azure_token: str, state: dict) -> None:
        self.state = state
        self.azure_token = azure_token
        self.url = self.state["api"]["url"]
        if not self.url:
            logger.error("[babylon] api url not found")
            sys.exit(1)
        self.organization_id = self.state["api"]["organization_id"]
        if not self.organization_id:
            logger.error("[babylon] Organization id is missing")
            sys.exit(1)
        self.solution_id = self.state["api"]["solution_id"]
        if not self.solution_id:
            logger.error("[babylon] solution id is missing")
            sys.exit(1)

    def add(self, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}/security/access",
            self.azure_token,
            type="POST",
            data=details,
        )
        return response

    def get(self, idendity_id: str):
        response = oauth_request(f"{self.url}/organizations/{self.organization_id}/solutions/ \
                {self.solution_id}/security/access/{idendity_id}",
                                 self.azure_token,
                                 type="GET")
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}/security",
            self.azure_token,
            type="GET")
        return response

    def set_default(self, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/ \
                {self.solution_id}/security/default",
            self.azure_token,
            type="POST",
            data=details,
        )
        return response

    def remove(self, identity_id: str):
        response = oauth_request(f"{self.url}/organizations/{self.organization_id}/solutions/ \
                {self.solution_id}/security/access/{identity_id}",
                                 self.azure_token,
                                 type="DELETE")
        return response

    def get_users(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}/security/users",
            self.azure_token,
            type="GET")
        return response

    def update(self, id: str, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/ \
                {self.solution_id}/security/access/{id}",
            self.azure_token,
            type="PATCH",
            data=details,
        )
        return response
