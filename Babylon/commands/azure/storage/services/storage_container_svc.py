import logging
import os
from glob import glob
from pathlib import Path

from azure.storage.blob import BlobServiceClient

from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class AzureStorageContainerService:
    def __init__(self, blob_client: BlobServiceClient, state: dict = None) -> None:
        self.blob_client = blob_client
        self.state = state

    def upload(self, org_id: str, work_id: str, dataset_id: str, folder: str):
        organization_id = org_id or self.state["api"]["organization_id"]
        workspace_id = work_id or self.state["api"]["workspace_id"]
        dataset_id = dataset_id or self.state["api"]["dataset.storage_id"]
        files = glob(os.path.join(folder, "*.csv"))
        check = self.blob_client.get_container_client(container=organization_id.lower())
        if not check.exists():
            logger.info(f"Container '{organization_id.lower()}' not found")
            return CommandResponse.fail()

        for f in files:
            client = self.blob_client.get_blob_client(
                container=organization_id.lower(),
                blob=f"{workspace_id.lower()}/datasets/{dataset_id}/{os.path.basename(f)}",
            )
            _f: Path = env.pwd / f
            with open(_f, "rb") as data:
                client.upload_blob(data)
        logger.info("Successfully uploaded")
