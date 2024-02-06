import os
import logging
import jmespath

from glob import glob
from pathlib import Path
from azure.core.exceptions import HttpResponseError
from Babylon.utils.checkers import check_ascii
from azure.storage.blob import BlobServiceClient
from Babylon.utils.environment import Environment
from Babylon.utils.interactive import confirm_deletion

from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class AzureStorageContainerService:

    def __init__(self, blob_client: BlobServiceClient, state: dict = None) -> None:
        self.blob_client = blob_client
        self.state = state

    def create(self, name: str):
        check_ascii(name)
        logger.info(
            f"Creating container {name} in storage account {self.blob_client.account_name}"
        )
        name = name.lower()
        try:
            container = self.blob_client.create_container(name)
            logger.info("Successfully created")
            return container
        except HttpResponseError as e:
            error_message = e.message.split("\n")
            logging.error(f"Failed to create container '{name}': {error_message[0]}")
            return CommandResponse.fail()
        except Exception as e:
            logger.error(e.message)
            return CommandResponse.fail()

    def delete(self, name: str, force_validation: bool):
        if not force_validation and not confirm_deletion("container", name):
            return CommandResponse.fail()
        try:
            container = self.blob_client.get_container_client(name)
            container.delete_container()
        except HttpResponseError as e:
            error_message = e.message.split("\n")
            logging.error(f"Failed to delete container '{name}': {error_message[0]}")
            return CommandResponse.fail()
        logger.info("Successfully deleted")

    def get_all(self, filter: bool):
        logger.info(
            f"Listing containers from storage account {self.blob_client.account_name}"
        )
        try:
            containers = self.blob_client.list_containers()
        except Exception as e:
            logger.error(e.message)
            return CommandResponse.fail()
        output_data = [
            {
                "name": container.name,
                "lease": container.lease,
                "etag": container.etag,
                "deleted": container.deleted,
                "public_access": container.public_access,
            }
            for container in containers
        ]
        if filter:
            output_data = jmespath.search(filter, output_data)
        return output_data

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
