import sys
import logging

from typing import Optional
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = logging.getLogger("Babylon")
env = Environment()


class SolutionService:

    def __init__(self, azure_token: str, state: dict, spec: Optional[dict] = None):
        self.state = state
        self.spec = spec
        self.azure_token = azure_token
        self.url = self.state["api"]["url"]
        self.organization_id = self.state["api"]["organization_id"]
        self.solution_id = self.state["api"]["solution_id"]
        if not self.organization_id:
            logger.error('organization id is missing')
            sys.exit(1)

    def create(self):
        payload = self.spec["payload"]
        if not payload.exists():
            print(f"file {payload} not found in directory")
            return None
        details = env.fill_template(payload)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions",
            self.azure_token,
            type="POST",
            data=details,
        )
        return response

    def delete(self, force_validation: bool):
        check_if_solution_exists(self.solution_id)
        if not force_validation and not confirm_deletion("solution", self.solution_id):
            return None
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
            self.azure_token,
            "DELETE",
        )
        return response

    def get(self):
        check_if_solution_exists(self.solution_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
            self.azure_token,
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions",
            self.azure_token,
        )
        return response

    def update(self):
        check_if_solution_exists(self.solution_id)
        payload = self.spec["payload"]
        if not payload.exists():
            print(f"file {payload} not found in directory")
            return None
        details = env.fill_template(payload)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
            self.azure_token,
            "PATCH",
            data=details,
        )
        return response


def check_if_solution_exists(solution_id: str):
    if solution_id is None:
        logger.error(f"solution {solution_id} is missing")
        sys.exit(1)
