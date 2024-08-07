import json
import sys
import logging

from typing import Optional
from Babylon.commands.api.solutions.services.solutions_security_svc import SolutionSecurityService
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
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions",
            self.azure_token,
            type="POST",
            data=details,
        )
        if response is None:
            logger.error('An error occurred while creating the solution')
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
        if response is None:
            logger.error(f"An error occurred while creating the solution id : {self.solution_id}")
        return response

    def get(self):
        check_if_solution_exists(self.solution_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
            self.azure_token,
        )
        if response is None:
            logger.error(f"An error occurred while getting the solution id : {self.solution_id}")
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions",
            self.azure_token,
        )
        if response is None:
            logger.error('An error occurred while getting all solutions')
        return response

    def update(self):
        check_if_solution_exists(self.solution_id)
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
            self.azure_token,
            "PATCH",
            data=details,
        )
        if response is None:
            logger.error(f"An error occurred while updating the solution id : {self.solution_id}")
        return response

    def update_security(self, old_security: dict):
        self.security_svc = SolutionSecurityService(azure_token=self.azure_token, state=self.state)
        payload = json.loads(self.spec["payload"])
        security_spec = payload.get("security")
        if not security_spec:
            logger.error("security is missing")
            sys.exit(1)
        ids_spec = [i.get("id") for i in security_spec["accessControlList"]]
        ids_existing = [i.get("id") for i in old_security["accessControlList"]]
        if "default" in security_spec:
            data = json.dumps(obj={"role": security_spec["default"]}, indent=2, ensure_ascii=True)
            response = self.security_svc.set_default(data)
            if response is None:
                logger.error('An error occurred while updating a default security role in solution')
                return None
        for g in security_spec["accessControlList"]:
            if g.get("id") in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = self.security_svc.update(id=g.get("id"), details=details)
                if response is None:
                    logger.error('An error occurred while updating a security role in solution')
                    return None
            if g.get("id") not in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = self.security_svc.add(details)
                if response is None:
                    logger.error('An error occurred while adding a security role in solution')
                    return None
        for s in ids_existing:
            if s not in ids_spec:
                response = self.security_svc.remove(id=s)
                if response is None:
                    logger.error('An error occurred while deleting a security role in solution')
                    return None
        return security_spec


def check_if_solution_exists(solution_id: str):
    if solution_id is None:
        logger.error(f"solution {solution_id} is missing")
        sys.exit(1)
