import sys
from logging import getLogger

from Babylon.utils.request import oauth_request
from Babylon.utils.interactive import confirm_deletion

logger = getLogger("Babylon")


class RunService:

    def __init__(self, keycloak_token: str, state: dict):
        self.state = state
        self.keycloak_token = keycloak_token
        self.url = self.state["api"]["url"]
        self.organization_id = self.state["api"]["organization_id"]
        self.workspace_id = self.state["api"]["workspace_id"]
        self.runner_id = self.state["api"]["runner_id"]
        self.run_id = self.state["api"]["run_id"]
        if not self.url:
            logger.error("[babylon] api url not found")
            sys.exit(1)
        if not self.organization_id:
            logger.error("[babylon] Organization id is missing verify the state")
            sys.exit(1)
        if not self.workspace_id:
            logger.error("[babylon] Workspace id is missing verify the state")
            sys.exit(1)
        if not self.runner_id:
            logger.error("[babylon] Runner id is missing verify the state")
            sys.exit(1)

    def logs(self):
        check_if_run_exists(self.run_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/runs/{self.run_id}/logs", self.keycloak_token)
        return response

    def status(self):
        check_if_run_exists(self.run_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/runs/{self.run_id}/status", self.keycloak_token)
        return response

    def delete(self, force_validation: bool):
        check_if_run_exists(self.run_id)
        if not force_validation and not confirm_deletion("workspace", self.run_id):
            return None
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/runs/{self.run_id}",
            self.keycloak_token,
            type="DELETE",
        )
        return response

    def get(self):
        check_if_run_exists(self.run_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/runs/{self.run_id}", self.keycloak_token)
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/runs", self.keycloak_token)
        return response


def check_if_run_exists(run_id: str):
    if not run_id:
        logger.error("[babylon] run_id is missing check the state or use --run-id")
        sys.exit(1)
