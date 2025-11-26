import json
import sys
from logging import getLogger
from typing import Optional

from Babylon.commands.api.runners.services.runner_security_svc import RunnerSecurityService
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = getLogger(__name__)


class RunnerService:

    def __init__(self, state: dict, config: dict, keycloak_token: str, spec: Optional[dict] = None):
        self.spec = spec
        self.state = state
        self.config = config
        self.url = config["api_url"]
        self.organization_id = state["organization_id"]
        self.workspace_id = state["workspace_id"]
        self.runner_id = self.state["runner_id"]
        self.keycloak_token = keycloak_token
        if not self.url:
            logger.error("api url not found verify the config in the k8s secret")
            sys.exit(1)
        if not self.organization_id:
            logger.error("Organization id is missing verify the state")
            sys.exit(1)
        if not self.workspace_id:
            logger.error("Workspace id is missing verify the state")
            sys.exit(1)

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}/runners",
            self.keycloak_token,
        )
        return response

    def get(self):
        check_if_runner_exists(self.runner_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}/runners/{self.runner_id}",
            self.keycloak_token,
        )
        return response

    def update(self):
        check_if_runner_exists(self.runner_id)
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}/runners/{self.runner_id}",
            self.keycloak_token,
            type="PATCH",
            data=details,
        )
        return response

    def create(self):
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}/runners",
            self.keycloak_token,
            type="POST",
            data=details,
        )
        return response

    def delete(self, force_validation: bool):
        check_if_runner_exists(self.runner_id)
        if not force_validation and not confirm_deletion("runner", self.runner_id):
            return None

        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}/runners/{self.runner_id}",
            self.keycloak_token,
            type="DELETE",
        )
        return response

    def start(self):
        check_if_runner_exists(self.runner_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/start",
            self.keycloak_token,
            type="POST",
        )
        return response

    def stop(self):
        check_if_runner_exists(self.runner_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/runners/{self.runner_id}/stop",
            self.keycloak_token,
            type="POST",
        )
        return response

    def update_security(self, old_security: dict):
        self.security_svc = RunnerSecurityService(keycloak_token=self.keycloak_token,
                                                  state=self.state,
                                                  config=self.config)
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
                return None
        for g in security_spec["accessControlList"]:
            if g.get("id") in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = self.security_svc.update(id=g.get("id"), details=details)
                if response is None:
                    return None
            if g.get("id") not in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = self.security_svc.add(details)
                if response is None:
                    return None
        for s in ids_existing:
            if s not in ids_spec:
                response = self.security_svc.delete(id=s)
                if response is None:
                    return None
        return security_spec


def check_if_runner_exists(runner_id: str):
    if not runner_id:
        logger.error("runner_id is missing check the state or use --runner-id")
        sys.exit(1)
