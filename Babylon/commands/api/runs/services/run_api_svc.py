import sys
from logging import getLogger

from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = getLogger(__name__)


class RunService:

    def __init__(self, keycloak_token: str, state: dict, config: dict):
        self.state = state
        self.config = config
        self.keycloak_token = keycloak_token
        self.url = config["api_url"]
        self.organization_id = self.state["organization_id"]
        self.workspace_id = self.state["workspace_id"]
        self.runner_id = self.state["runner_id"]
        self.run_id = self.state["run_id"]
        if not self.url:
            logger.error("api url not found verify the config in the k8s secret")
            sys.exit(1)
        if not self.organization_id:
            logger.error("Organization id is missing verify the state")
            sys.exit(1)
        if not self.workspace_id:
            logger.error("Workspace id is missing verify the state")
            sys.exit(1)
        if not self.runner_id:
            logger.error("Runner id is missing verify the state")
            sys.exit(1)

    def logs(self):
        check_if_run_exists(self.run_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/runs/{self.run_id}/logs",
            self.keycloak_token,
        )
        return response

    def status(self):
        check_if_run_exists(self.run_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/runs/{self.run_id}/status",
            self.keycloak_token,
        )
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
            f"{self.workspace_id}/runners/{self.runner_id}/runs/{self.run_id}",
            self.keycloak_token,
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/runs",
            self.keycloak_token,
        )
        return response


def check_if_run_exists(run_id: str):
    if not run_id:
        logger.error("run_id is missing check the state or use --run-id")
        sys.exit(1)
