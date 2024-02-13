import sys

from logging import getLogger
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


class DatasetSecurityService:

    def __init__(self, azure_token: str, state: dict) -> None:
        self.state = state
        self.azure_token = azure_token
        self.url = self.state["api"]["url"]
        if not self.url:
            logger.error("API url not found")
            sys.exit(1)
        self.organization_id = self.state["api"]["organization_id"]
        if not self.organization_id:
            logger.error("organization id is missing")
            sys.exit(1)
        self.dataset_id = self.state["api"]["dataset_id"]
        if not self.dataset_id:
            logger.error("dataset id is missing")
            sys.exit(1)

    def add(self, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets/{self.dataset_id}/security/access",
            self.azure_token,
            type="POST",
            data=details,
        )
        return response

    def get(self, id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets/{self.dataset_id}/security/{id}",
            self.azure_token,
            type="GET",
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets/{self.dataset_id}/security",
            self.azure_token,
            type="GET",
        )
        return response

    def update(self, id: str, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets/{self.dataset_id}/security/{id}",
            self.azure_token,
            type="PATH",
            data=details)
        return response

    def set_default(self, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets/{self.dataset_id}/security/{id}",
            self.azure_token,
            type="PATH",
            data=details)
        return response

    def delete(self, id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets/{self.dataset_id}/security/{id}",
            self.azure_token,
            type="DELETE")
        return response
