import json
import logging
import sys
from typing import Optional

from Babylon.commands.api.solutions.services.solutions_security_svc import SolutionSecurityService
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = logging.getLogger(__name__)
env = Environment()


class SolutionService:

    def __init__(self, keycloak_token: str, config: dict, state: dict, spec: Optional[dict] = None):
        self.state = state
        self.config = config
        self.spec = spec
        self.keycloak_token = keycloak_token
        self.url = config["api_url"]
        self.organization_id = self.state["organization_id"]
        self.solution_id = self.state["solution_id"]
        if not self.url:
            logger.error("api url not found verify the config in the k8s secret")
            sys.exit(1)
        if not self.organization_id:
            logger.error("Organization id is missing verify the state")
            sys.exit(1)

    def create(self):
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions",
            self.keycloak_token,
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
            self.keycloak_token,
            "DELETE",
        )
        return response

    def get(self):
        check_if_solution_exists(self.solution_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
            self.keycloak_token,
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions",
            self.keycloak_token,
        )
        return response

    def update(self):
        check_if_solution_exists(self.solution_id)
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
            self.keycloak_token,
            "PATCH",
            data=details,
        )
        return response

    def update_security(self, old_security: dict):
        self.security_svc = SolutionSecurityService(keycloak_token=self.keycloak_token,
                                                    state=self.state,
                                                    config=self.config)
        payload = json.loads(self.spec["payload"])
        security_spec = payload.get("security")
        if not security_spec:
            logger.error("Security is missing")
            sys.exit(1)
        ids_spec = [i.get("id") for i in security_spec["accessControlList"]]
        ids_existing = [i.get("id") for i in old_security["accessControlList"]]
        if "default" in security_spec:
            data = json.dumps(obj={"role": security_spec["default"]}, indent=2, ensure_ascii=True)
            response = self.security_svc.set_default(data)
            if response is None:
                return CommandResponse.fail()
        for g in security_spec["accessControlList"]:
            if g.get("id") in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = self.security_svc.update(id=g.get("id"), details=details)
                if response is None:
                    return CommandResponse.fail()
            if g.get("id") not in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = self.security_svc.add(details)
                if response is None:
                    return CommandResponse.fail()
        for s in ids_existing:
            if s not in ids_spec:
                response = self.security_svc.delete(id=s)
                if response is None:
                    return CommandResponse.fail()
        return security_spec


def check_if_solution_exists(solution_id: str):
    if solution_id is None:
        logger.error("solution_id is missing check the state or use --solution-id")
        sys.exit(1)
