import sys

from typing import Optional
from logging import getLogger
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


class SolutionRunTemplatesService:

    def __init__(self, keycloak_token: str, state: dict, spec: Optional[dict] = None) -> None:
        self.state = state
        self.spec = spec
        self.keycloak_token = keycloak_token
        self.url = self.state["api"]["url"]
        if not self.url:
            logger.error("[babylon] api url not found verify the state")
            sys.exit(1)
        self.organization_id = self.state["api"]["organization_id"]
        if not self.organization_id:
            logger.error("[babylon] Organization id is missing verify the state")
            sys.exit(1)
        self.solution_id = self.state["api"]["solution_id"]
        if not self.solution_id:
            logger.error("[babylon] Solution id is missing verify the state")
            sys.exit(1)

    def add(self):
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}/runTemplates",
            self.keycloak_token,
            type="POST",
            data=details,
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}/runTemplates",
            self.keycloak_token,
            type="GET")
        return response

    def get(self, run_template_id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/"
            f"{self.solution_id}/runTemplates/{run_template_id}",
            self.keycloak_token,
            type="GET")
        return response

    def delete(self, run_template_id: str):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/"
            f"{self.solution_id}/runTemplates/{run_template_id}",
            self.keycloak_token,
            type="DELETE")
        return response

    def update(self, run_template_id: str):
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/"
            f"{self.solution_id}/runTemplates/{run_template_id}",
            self.keycloak_token,
            type="PATCH",
            data=details,
        )
        return response
