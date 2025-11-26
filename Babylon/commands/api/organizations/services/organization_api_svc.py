import json
import sys
from logging import getLogger

from Babylon.commands.api.organizations.services.organization_security_svc import (
    OrganizationSecurityService,
)
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

logger = getLogger(__name__)
env = Environment()


class OrganizationService:

    def __init__(self, config: dict, state: dict, keycloak_token: str, spec: dict = None):
        self.config = config
        self.spec = spec
        self.state = state
        self.keycloak_token = keycloak_token
        self.url = config["api_url"]
        if not self.url:
            logger.error("api url not found verify the config in the k8s secret")
            sys.exit(1)

    def create(self):
        details = self.spec["payload"]
        response = oauth_request(f"{self.url}/organizations", self.keycloak_token, type="POST", data=details)
        return response

    def delete(self, force_validation: bool):
        organization_id = self.state["organization_id"]
        check_if_organization_exists(organization_id)
        if not force_validation and not confirm_deletion("organization", organization_id):
            return None
        response = oauth_request(
            f"{self.url}/organizations/{organization_id}",
            self.keycloak_token,
            type="DELETE",
        )
        return response

    def get(self):
        organization_id = self.state["organization_id"]
        check_if_organization_exists(organization_id)
        response = oauth_request(f"{self.url}/organizations/{organization_id}", self.keycloak_token)
        return response

    def get_all(self):
        response = oauth_request(f"{self.url}/organizations", self.keycloak_token)
        return response

    def update(self):
        organization_id = self.state["organization_id"]
        check_if_organization_exists(organization_id)
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{organization_id}",
            self.keycloak_token,
            type="PATCH",
            data=details,
        )
        return response

    def update_security(self, old_security: dict):
        self.security_svc = OrganizationSecurityService(keycloak_token=self.keycloak_token,
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


def check_if_organization_exists(dataset_id: str):
    if not dataset_id:
        logger.error("organization_id is missing check the state or use --organization-id")
        sys.exit(1)
