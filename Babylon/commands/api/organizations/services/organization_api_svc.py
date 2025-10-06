import json
import sys

from logging import getLogger
from Babylon.commands.api.organizations.services.organization_security_svc import (
    OrganizationSecurityService, )
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


class OrganizationService:

    def __init__(self, state: dict, keycloak_token: str, spec: dict = None):
        self.state = state
        self.spec = spec
        self.keycloak_token = keycloak_token
        self.url = state["api"]["url"]
        if not self.url:
            logger.error("API url not found")
            sys.exit(1)

    def create(self):
        details = self.spec["payload"]
        response = oauth_request(f"{self.url}/organizations", self.keycloak_token, type="POST", data=details)
        if response is None:
            logger.error('An error occurred while creating the organisation')
        return response

    def delete(self, force_validation: bool):
        organization_id = self.state["api"]["organization_id"]
        if not organization_id:
            logger.error("organization id not found")
            sys.exit(1)
        if not force_validation and not confirm_deletion("organization", organization_id):
            return None
        response = oauth_request(
            f"{self.url}/organizations/{organization_id}",
            self.azure_token,
            type="DELETE",
        )
        if response is None:
            logger.error(f'An error occurred while deleting the organisation with id: {organization_id}')
        return response

    def get(self):
        organization_id = self.state["api"]["organization_id"]
        if not organization_id:
            logger.error("Organization id is missing")
            return None
        response = oauth_request(f"{self.url}/organizations/{organization_id}", self.azure_token)
        if response is None:
            logger.error(f"An error occurred while getting the organisation with id: {organization_id}")
        return response

    def get_all(self):
        response = oauth_request(f"{self.url}/organizations", self.azure_token)
        if response is None:
            logger.error('An error occurred while getting of all organisations')
        return response

    def update(self):
        details = self.spec["payload"]
        organization_id = self.state["api"]["organization_id"]
        response = oauth_request(
            f"{self.url}/organizations/{organization_id}",
            self.azure_token,
            type="PATCH",
            data=details,
        )
        if response is None:
            logger.error(f"An error occurred while updating the organisation with id: {organization_id}")
        return response

    def update_security(self, old_security: dict):
        self.security_svc = OrganizationSecurityService(azure_token=self.azure_token, state=self.state)
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
                logger.error('An error occurred while updating a default security role in organization')
                return None
        for g in security_spec["accessControlList"]:
            if g.get("id") in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = self.security_svc.update(id=g.get("id"), details=details)
                if response is None:
                    logger.error('An error occurred while updating a security role in organization')
                    return None
            if g.get("id") not in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = self.security_svc.add(details)
                if response is None:
                    logger.error('An error occurred while adding a security role in organization')
                    return None
        for s in ids_existing:
            if s not in ids_spec:
                response = self.security_svc.delete(id=s)
                if response is None:
                    logger.error('An error occurred while deleting a security role in organization')
                    return None
        return security_spec
