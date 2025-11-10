import json
import logging
import sys

from typing import Optional
from Babylon.commands.api.datasets.services.datasets_security_svc import DatasetSecurityService
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.request import oauth_request
from Babylon.utils.response import CommandResponse

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
        self.dataset_id = self.state["api"]["dataset_id"]
        if not self.url:
            logger.error("[babylon] api url not found verify the state")
            sys.exit(1)
        if not self.organization_id:
            logger.error("[babylon] Organization id is missing verify the state")
            sys.exit(1)
        if not self.workspace_id:
            logger.error('[babylon] Workspace id is missing verify the state')
            sys.exit(1)

    def delete(self, force_validation: bool):
        check_if_dataset_exists(self.dataset_id)
        if not force_validation and not confirm_deletion("dataset", self.dataset_id):
            return None
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/"
            f"workspaces/{self.workspace_id}/datasets/{self.dataset_id}",
            self.keycloak_token,
            type="DELETE",
        )
        return response

    def delete_part(self, dataset_part_id: str, force_validation: bool):
        if not force_validation and not confirm_deletion("dataset part", dataset_part_id):
            return None
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/"
            f"workspaces/{self.workspace_id}/datasets/{self.dataset_id}/"
            f"parts/{dataset_part_id}",
            self.keycloak_token,
            type="DELETE",
        )
        return response

    def download_part(self, dataset_part_id: str):
        check_if_dataset_exists(self.dataset_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/"
            f"workspaces/{self.workspace_id}/datasets/{self.dataset_id}/"
            f"parts/{dataset_part_id}/download",
            self.keycloak_token,
            type="GET",
        )
        return response

    def get_all(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}/datasets",
            self.keycloak_token,
            type="GET",
        )
        return response

    def get(self):
        check_if_dataset_exists(self.dataset_id)
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/"
            f"workspaces/{self.workspace_id}/datasets/{self.dataset_id}",
            self.keycloak_token,
            type="GET",
        )
        return response

    def get_part(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/"
            f"workspaces/{self.workspace_id}/datasets/{self.dataset_id}/"
            f"parts/{self.state['api']['dataset_part_id']}",
            self.keycloak_token,
            type="GET",
        )
        return response

    def get_all_parts(self):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/"
            f"workspaces/{self.workspace_id}/datasets/{self.dataset_id}/parts",
            self.keycloak_token,
            type="GET",
        )
        return response

    def create(self, filename_array: list[str]):
        url = f"{self.url}/organizations/{self.organization_id}/workspaces/{self.workspace_id}/datasets"
        data = {"datasetCreateRequest": self.spec["payload"]}
        files = [("files", (filename, open(filename, "rb"), "text/csv")) for filename in filename_array]
        response = oauth_request(
            url=url,
            access_token=self.keycloak_token,
            type="POST",
            content_type="multipart/form-data",
            files=files,
            data=data,
        )
        return response

    def create_part(self, filename: str):
        url = (f"{self.url}/organizations/{self.organization_id}"
               f"/workspaces/{self.workspace_id}"
               f"/datasets/{self.dataset_id}/parts")
        data = {"datasetPartCreateRequest": self.spec["payload"]}
        files = [("file", (filename, open(filename, "rb"), "text/csv"))]
        response = oauth_request(
            url=url,
            access_token=self.keycloak_token,
            type="POST",
            content_type="multipart/form-data",
            files=files,
            data=data,
        )
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
            logger.error("[babylon] Security is missing")
            sys.exit(1)
        ids_spec = [i.get("id") for i in security_spec["accessControlList"]]
        ids_existing = [i.get("id") for i in old_security["accessControlList"]]
        if "default" in security_spec:
            data = json.dumps(obj={"role": security_spec["default"]}, indent=2, ensure_ascii=True)
            response = security_svc.set_default(data)
            if response is None:
                return CommandResponse.fail()
        for g in security_spec["accessControlList"]:
            if g.get("id") in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = security_svc.update(id=g.get("id"), details=details)
                if response is None:
                    return CommandResponse.fail()
            if g.get("id") not in ids_existing:
                details = json.dumps(obj=g, indent=2, ensure_ascii=True)
                response = security_svc.add(details)
                if response is None:
                    return CommandResponse.fail()
        for s in ids_existing:
            if s not in ids_spec:
                response = security_svc.delete(id=s)
                if response is None:
                    return CommandResponse.fail()
        return security_spec


def check_if_dataset_exists(dataset_id: str):
    if not dataset_id:
        logger.error("[babylon] dataset_id is missing check the state or use --dataset-id")
        sys.exit(1)
