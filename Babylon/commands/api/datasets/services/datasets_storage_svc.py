import logging

from pathlib import Path
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


class DatasetStorageService:

    def __init__(self, azure_token: str, state: dict) -> None:
        self.state = state
        self.azure_token = azure_token
        self.organization_id = self.state["api"]["organization_id"]
        self.account_secret = env.get_platform_secret(platform=env.environ_id, resource="storage", name="account")

    def upload_csv_to_storage(self, path: Path, dataset_dir_name: str, dataset_name: str, override: bool):
        workspace_id = self.state["api"]["workspace_id"]
        check = env.blob_client.get_container_client(container=self.organization_id)
        if not check.exists():
            logger.info(f"[azure] container '{self.organization_id}' not found")
            return None
        client = env.blob_client.get_blob_client(
            container=self.organization_id,
            blob=f"{workspace_id}/datasets/{dataset_dir_name}/{dataset_name}",
        )
        if override and client.exists():
            client.delete_blob()
        with open(path, "rb") as data:
            client.upload_blob(data)
        logger.info(f"[azure] successfully sent dataset file : {dataset_name} to workspace {workspace_id}")
