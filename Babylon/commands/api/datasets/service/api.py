import json
import logging
import sys

from typing import Optional

from Babylon.commands.api.datasets.security.service.api import DatasetSecurityService
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request

logger = logging.getLogger("Babylon")
env = Environment()


class DatasetService:

    def __init__(self, azure_token: str, state: dict, spec: Optional[dict] = None) -> None:
        self.state = state
        self.spec = spec
        self.azure_token = azure_token
        self.url = self.state["api"]["url"]
        self.organization_id = self.state["api"]["organization_id"]

        if not self.url:
            logger.error("API url not found")
            sys.exit(1)
        if not self.organization_id:
            logger.error("organization_id not found")
            sys.exit(1)

    def create(self):
        details = self.spec["payload"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets",
            self.azure_token,
            type="POST",
            data=details,
        )
        return response

    def delete(self, force_validation: bool):
        dataset_id = self.state["api"]["dataset_id"]
        if not force_validation and not confirm_deletion("dataset", dataset_id):
            return None
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets/{dataset_id}",
            self.azure_token,
            type="DELETE",
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets",
            self.azure_token,
        )
        return response

    def get(self):
        dataset_id = self.state["api"]["dataset_id"]
        if not dataset_id:
            logger.error("dataset_id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets/{dataset_id}",
            self.azure_token,
        )
        if response is None:
            return None
        dataset = response.json()
        return dataset

    def search(self, tag: str):
        details = {"datasetTags": [tag]}
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets/search",
            self.azure_token,
            type="POST",
            json=details,
        )
        return response

    def update(self):
        dataset_id = self.state["api"]["dataset_id"]
        details = self.spec["payload"]
        if not dataset_id:
            logger.error("dataset_id not found")
            sys.exit(1)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/datasets/{dataset_id}",
            self.azure_token,
            type="PATCH",
            data=details,
        )
        return response

    def update_security(self, old_security: dict):
        self.security_svc = DatasetSecurityService(azure_token=self.azure_token, state=self.state)
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
                response = self.security_svc.update(id=g.get("id"), details=details)
                if response is None:
                    return None
        for s in ids_existing:
            if s not in ids_spec:
                response = self.security_svc.delete(id=s)
                if response is None:
                    return None
        return security_spec
