import sys
from logging import getLogger

from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")


class RunnerSecurityService:

    def __init__(self, keycloak_token: str, state: dict) -> None:
        self.state = state
        self.keycloak_token = keycloak_token
        self.url = self.state["api"]["url"]
        self.organization_id = self.state["api"]["organization_id"]
        self.workspace_id = self.state["api"]["workspace_id"]
        self.runner_id = self.state["api"]["runner_id"]
        if not self.url:
            logger.error("[babylon] api url not found verify the state")
            sys.exit(1)
        if not self.organization_id:
            logger.error("[babylon] Organization id is missing verify the state")
            sys.exit(1)
        if not self.workspace_id:
            logger.error('[babylon] Workspace id is missing verify the state')
            sys.exit(1)
        if not self.runner_id:
            logger.error("[babylon] Runner id is missing verify the state")
            sys.exit(1)

    def get(self, id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/security/access/{id}",
            self.keycloak_token,
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/security",
            self.keycloak_token,
        )
        return response

    def add(self, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/security/access",
            self.keycloak_token,
            type="POST",
            data=details,
        )
        return response

    def update(self, id: str, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/security/access/{id}",
            self.keycloak_token,
            type="PATCH",
            data=details,
        )
        return response

    def delete(self, id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/security/access/{id}",
            self.keycloak_token,
            type="DELETE",
        )
        return response

    def set_default(self, details: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/security/default",
            self.keycloak_token,
            type="PATCH",
            data=details,
        )
        return response
