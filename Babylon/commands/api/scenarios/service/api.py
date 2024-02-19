import sys
import json

from logging import getLogger

from typing import Optional

from Babylon.commands.api.scenarios.security.service.api import ScenarioSecurityService
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")


class ScenarioService:

    def __init__(self, state: dict, azure_token: str, spec: Optional[dict] = None):
        self.spec = spec
        self.state = state
        self.url = state["api"]["url"]
        self.organization_id = state["api"]["organization_id"]
        self.workspace_id = state["api"]["workspace_id"]
        self.azure_token = azure_token

        if not self.url:
            logger.error("API url not found")
            sys.exit(1)
        if not self.organization_id:
            logger.error("organization_id not found")
            sys.exit(1)
        if not self.workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios",
            self.azure_token,
        )
        return response

    def get(self):
        scenario_id = self.state["api"]["scenario_id"]

        if not scenario_id:
            logger.error("scenario_id is missing")
            sys.exit(1)

        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
        )
        return response

    def update(self):
        scenario_id = self.state["api"]["scenario_id"]

        if not scenario_id:
            logger.error("scenario_id is missing")
            sys.exit(1)

        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
            type="PATCH",
            data=details,
        )
        return response

    def create(self):
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios",
            self.azure_token,
            type="POST",
            data=details,
        )
        return response

    def delete(self, force_validation: bool):
        scenario_id = self.state["api"]["scenario_id"]

        if not scenario_id:
            logger.error("scenario_id is missing")
            sys.exit(1)

        if not force_validation and not confirm_deletion("solution", scenario_id):
            return None

        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{scenario_id}",
            self.azure_token,
            type="DELETE",
        )
        return response

    def run(self):
        scenario_id = self.state["api"]["scenario_id"]

        if not scenario_id:
            logger.error("scenario_id is missing")
            sys.exit(1)

        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/"
            f"{self.workspace_id}/scenarios/{scenario_id}/run",
            self.azure_token,
            type="POST",
        )
        return response

    def update_security(self, old_security: dict):
        self.security_svc = ScenarioSecurityService(azure_token=self.azure_token, state=self.state)
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
