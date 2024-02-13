import json
import sys

from logging import getLogger
from Babylon.commands.api.organizations.security.service.api import (
    OrganizationSecurityService, )
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


class OrganizationService:

    def __init__(self, state: dict, azure_token: str, spec: dict = None):
        self.state = state
        self.spec = spec
        self.azure_token = azure_token
        self.url = state["api"]["url"]
        if not self.url:
            logger.error("API url not found")
            sys.exit(1)

    def create(self):
        details = self.spec["payload"]
        response = oauth_request(f"{self.url}/organizations", self.azure_token, type="POST", data=details)
        return response

    def delete(self, force_validation: bool):
        organization_id = self.state["api"]["organization_id"]
        if not force_validation and not confirm_deletion("organization", organization_id):
            return None
        organization_id = self.state["api"]["organization_id"]
        if not organization_id:
            logger.error("organization id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{organization_id}",
            self.azure_token,
            type="DELETE",
        )
        return response

    def get(self):
        organization_id = self.state["api"]["organization_id"]
        if not organization_id:
            logger.error("Organization id is missing")
            return None
        response = oauth_request(f"{self.url}/organizations/{organization_id}", self.azure_token)
        return response

    def get_all(self):
        return oauth_request(f"{self.url}/organizations", self.azure_token)

    def update(self):
        details = self.spec["payload"]
        organization_id = self.states["api"]["organization_id"]
        response = oauth_request(
            f"{self.url}/organizations/{organization_id}",
            self.azure_token,
            type="PATCH",
            data=details,
        )
        return response

    def security(self, data: dict):
        self.security_svc = OrganizationSecurityService(azure_token=self.azure_token, state=self.state)
        security_spec = self.spec["payload"].get("security")
        if not security_spec:
            logger.error("security is missing")
            sys.exit(1)
        organization_id = self.state["api"]["organization_id"]
        ids_spec = [i.get("id") for i in security_spec["accessControlList"]]
        ids_existing = [i.get("id") for i in data["security"]["accessControlList"]]
        if "default" in security_spec:
            data = json.dumps(obj={"role": security_spec["default"]}, indent=2, ensure_ascii=True)
            response = oauth_request(
                f"{self.url}/organizations/{organization_id}/security/default",
                access_token=self.azure_token,
                type="POST",
                data=data,
            )
            if response is None:
                return None
        for s in ids_existing:
            if s not in ids_spec:
                response = self.security_svc.delete(s.get("id"))
                if response is None:
                    return None
        for g in security_spec["accessControlList"]:
            if g.get("id") in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = self.security_svc.update(g.get("id"), details=details)
                if response is None:
                    return None
            if g.get("id") not in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = self.security_svc.add(details)
                if response is None:
                    return None
        return self
