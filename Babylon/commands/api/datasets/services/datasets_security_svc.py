import sys
from logging import getLogger

from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request

logger = getLogger(__name__)
env = Environment()


class DatasetSecurityService:

    def __init__(self, keycloak_token: str, state: dict, config: dict) -> None:
        self.state = state
        self.config = config
        self.keycloak_token = keycloak_token
        self.url = config["api_url"]
        if not self.url:
            logger.error("api url not found verify the config in the k8s secret")
            sys.exit(1)
        self.organization_id = self.state["organization_id"]
        if not self.organization_id:
            logger.error("Organization id is missing verify the state")
            sys.exit(1)
        self.workspace_id = self.state["workspace_id"]
        if not self.workspace_id:
            logger.error('Workspace id is missing verify the state')
            sys.exit(1)
        self.dataset_id = self.state["dataset_id"]
        if not self.dataset_id:
            logger.error('Dataset is missing verify the state')
            sys.exit(1)

    def add(self, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/"
            f"workspaces/{self.workspace_id}/"
            f"datasets/{self.dataset_id}/security/access",
            self.keycloak_token,
            type="POST",
            data=details,
        )
        return response

    def get(self, id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}"
            f"/workspaces/{self.workspace_id}/"
            f"datasets/{self.dataset_id}/security/access/{id}",
            self.keycloak_token,
            type="GET",
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}"
            f"/workspaces/{self.workspace_id}/"
            f"datasets/{self.dataset_id}/security/users",
            self.keycloak_token,
            type="GET",
        )
        return response

    def update(self, id: str, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}"
            f"/workspaces/{self.workspace_id}/"
            f"datasets/{self.dataset_id}/security/access/{id}",
            self.keycloak_token,
            type="PATCH",
            data=details,
        )
        return response

    def set_default(self, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/"
            f"workspaces/{self.workspace_id}/"
            f"datasets/{self.dataset_id}/security/default",
            self.keycloak_token,
            type="PATCH",
            data=details,
        )
        return response

    def delete(self, id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/"
            f"workspaces/{self.workspace_id}/"
            f"datasets/{self.dataset_id}/security/access/{id}",
            self.keycloak_token,
            type="DELETE",
        )
        return response
