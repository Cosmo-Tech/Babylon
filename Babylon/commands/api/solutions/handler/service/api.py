import os
import sys
import zipfile

from logging import getLogger
from pathlib import Path
from posixpath import basename
from Babylon.services.blob import blob_client
from Babylon.utils.environment import Environment
from Babylon.utils.request import oauth_request

logger = getLogger("Babylon")
env = Environment()


class SolutionHandleService:

    def __init__(self, azure_token: str, state: dict) -> None:
        self.state = state
        self.azure_token = azure_token
        self.account_secret = env.get_platform_secret(platform=env.environ_id, resource="storage", name="account")
        self.url = state["api"].get("url")
        if not self.url:
            logger.error("url api is missing")
            sys.exit(1)
        self.organization_id = state["api"].get("organization_id")
        if not self.organization_id:
            logger.error("organization id is missing")
            sys.exit(1)
        self.solution_id = state["api"].get("solution_id")
        if not self.solution_id:
            logger.error("solution id is missing")
            sys.exit(1)

    def download(self, run_template_id: str, handler_id: str):
        storage_name = self.state["azure"]["storage_account_name"]
        check = blob_client(storage_name=storage_name,
                            account_secret=self.account_secret).get_container_client(container=self.organization_id)
        if not check.exists():
            logger.info(f"Container '{self.organization_id}' not found")
            sys.exit(1)
        client = blob_client(storage_name=storage_name, account_secret=self.account_secret).get_blob_client(
            container=self.organization_id,
            blob=f"{self.solution_id}/{run_template_id}/{handler_id}.zip",
        )
        data = client.download_blob().readall()
        zf = zipfile.ZipFile("data.zip", mode="w", compression=zipfile.ZIP_DEFLATED)
        zf.writestr(basename(client.blob_name), data)
        zf.extractall(".")
        os.remove("data.zip")
        logger.info("Successfully downloaded handler file")

    def upload(self, run_template_id: str, handler_id: str, handler_path: Path, override: bool):
        storage_name = self.state["azure"]["storage_account_name"]
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
            self.azure_token,
            type="GET",
        )
        solution = response.json()
        run_templates = list(map(lambda x: x["id"], solution["runTemplates"]))
        if run_template_id not in run_templates:
            logger.info(f"Invalid runTemplateId: {run_template_id}. Must be one of: {run_templates}")
            return None
        if not handler_path.suffix == ".zip":
            logger.error("solution handler upload only supports zip files")
            return None
        check = blob_client(storage_name=storage_name,
                            account_secret=self.account_secret).get_container_client(container=self.organization_id)
        if not check.exists():
            logger.info(f"Container '{self.organization_id}' not found")
            return None
        client = blob_client(storage_name=storage_name, account_secret=self.account_secret).get_blob_client(
            container=self.organization_id,
            blob=f"{self.solution_id}/{run_template_id}/{handler_id}.zip",
        )
        if override and client.exists():
            client.delete_blob()
        with open(handler_path, "rb") as data:
            client.upload_blob(data)
        logger.info(f"Successfully sent handler file to solution {self.solution_id}")
