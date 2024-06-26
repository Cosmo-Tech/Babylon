import os
import sys
import zipfile

from logging import getLogger
from pathlib import Path
from posixpath import basename
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
            logger.error("[api] organization id is missing")
            sys.exit(1)
        self.solution_id = state["api"].get("solution_id")
        if not self.solution_id:
            logger.error("[api] solution id is missing")
            sys.exit(1)

    def download(self, run_template_id: str, handler_id: str):
        check = env.blob_client.get_container_client(container=self.organization_id)
        if not check.exists():
            logger.info(f"[api] container '{self.organization_id}' not found")
            sys.exit(1)
        client = env.blob_client.get_blob_client(
            container=self.organization_id,
            blob=f"{self.solution_id}/{run_template_id}/{handler_id}.zip",
        )
        if not client.exists():
            logger.info("[api] handler file not found")
            sys.exit(1)
        data = client.download_blob().readall()
        zf = zipfile.ZipFile(f"{handler_id}.zip", mode="w", compression=zipfile.ZIP_DEFLATED)
        zf.writestr(basename(client.blob_name), data)
        zf.extractall(".")
        os.remove(f"{handler_id}.zip")
        logger.info("[api] successfully downloaded handler file")

    def upload(self, run_template_id: str, handler_id: str, handler_path: Path, override: bool):
        response = oauth_request(
            f"{self.url}/organizations/{self.organization_id}/solutions/{self.solution_id}",
            self.azure_token,
            type="GET",
        )
        solution = response.json()
        run_templates = list(map(lambda x: x["id"], solution["runTemplates"]))
        if run_template_id not in run_templates:
            logger.info(f"[api] invalid runTemplateId: {run_template_id}. Must be one of: {run_templates}")
            return None
        if not handler_path.suffix == ".zip":
            logger.error("[api] solution handler upload only supports zip files")
            return None
        check = env.blob_client.get_container_client(container=self.organization_id)
        if not check.exists():
            logger.info(f"[azure] container '{self.organization_id}' not found")
            return None
        client = env.blob_client.get_blob_client(
            container=self.organization_id,
            blob=f"{self.solution_id}/{run_template_id}/{handler_id}.zip",
        )
        if override and client.exists():
            client.delete_blob()
        with open(handler_path, "rb") as data:
            client.upload_blob(data)
        logger.info(
            f"[azure] successfully sent handler '{handler_id}' to '{run_template_id}' in solution '{self.solution_id}'")
