import json
import logging
import sys

from typing import Optional

from pathlib import Path

from Babylon.commands.api.datasets.services.datasets_security_svc import DatasetSecurityService
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = logging.getLogger("Babylon")
env = Environment()


class DatasetService:

    def __init__(self, keycloak_token: str, state: dict, spec: Optional[dict] = None) -> None:
        self.state = state
        self.spec = spec
        self.keycloak_token = keycloak_token
        self.url = self.state["api"]["url"]
        self.organization_id = self.state["api"]["organization_id"]
        self.workspace_id = self.state["api"]["workspace_id"]

        if not self.url:
            logger.error("API url not found")
            sys.exit(1)
        if not self.organization_id:
            logger.error("organization_id not found")
            sys.exit(1)
        if not self.workspace_id:
            logger.error("workspace_id not found")
            sys.exit(1)

    def delete(self, dataset_id: str, force_validation: bool):
        if not force_validation and not confirm_deletion("dataset", dataset_id):
            return None
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}/datasets/{dataset_id}",
            self.keycloak_token,
            type="DELETE",
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}/datasets",
            self.keycloak_token,
            type="GET",
        )
        return response

    def get(self, dataset_id: str):
        if not dataset_id:
            logger.error("dataset_id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}/datasets/{dataset_id}",
            self.keycloak_token,
        )
        if response is None:
            return None
        return response

    def search(self, tag: str):
        details = {"datasetTags": [tag]}
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}/datasets/search",
            self.keycloak_token,
            type="POST",
            json=details,
        )
        return response

    def update_security(self, old_security: dict):
        security_svc = DatasetSecurityService(keycloak_token=self.keycloak_token, state=self.state)
        payload = json.loads(self.spec["payload"])
        security_spec = payload.get("security")
        if not security_spec:
            logger.error("security is missing")
            sys.exit(1)
        ids_spec = [i.get("id") for i in security_spec["accessControlList"]]
        ids_existing = [i.get("id") for i in old_security["accessControlList"]]
        if "default" in security_spec:
            data = json.dumps(obj={"role": security_spec["default"]}, indent=2, ensure_ascii=True)
            response = security_svc.set_default(data)
            if response is None:
                return None
        for g in security_spec["accessControlList"]:
            if g.get("id") in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = security_svc.update(id=g.get("id"), details=details)
                if response is None:
                    return None
            if g.get("id") not in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = security_svc.add(details)
                if response is None:
                    return None
        for s in ids_existing:
            if s not in ids_spec:
                response = security_svc.delete(id=s)
                if response is None:
                    return None
        return security_spec