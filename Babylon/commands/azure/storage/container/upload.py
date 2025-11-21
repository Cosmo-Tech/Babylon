import logging
import pathlib
from typing import Any, Optional

from azure.storage.blob import BlobServiceClient
from click import Path, command, option

from Babylon.commands.azure.storage.services.storage_container_svc import AzureStorageContainerService
from Babylon.utils.clients import pass_blob_client
from Babylon.utils.decorators import injectcontext, retrieve_state
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_blob_client
@option(
    "--folder",
    "folder",
    required=True,
    type=Path(readable=True, dir_okay=True, exists=True, path_type=pathlib.Path),
    help="Folder with cvs files to upload",
)
@option("--organization-id", "org_id", help="Organization id")
@option("--workspace-id", "work_id", help="Workspace id")
@option("--dataset-id", "dataset_id", help="Dataset id")
@retrieve_state
def upload(
    state: Any,
    blob_client: BlobServiceClient,
    org_id: str,
    work_id: str,
    dataset_id: str,
    folder: Optional[Path] = None,
) -> CommandResponse:
    """
    Upload csv files to blob storage container
    """
    service = AzureStorageContainerService(blob_client=blob_client, state=state)
    service.upload(
        org_id=org_id,
        work_id=work_id,
        dataset_id=dataset_id,
        folder=folder,
    )
    return CommandResponse.success()
