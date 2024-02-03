import logging
import pathlib

from typing import Any, Optional
from azure.storage.blob import BlobServiceClient
from click import Path, command, option
from Babylon.commands.azure.storage.container.service.api import AzureStorageContainerService
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.clients import pass_blob_client
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@timing_decorator
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
@inject_context_with_resource(
    {
        "api": ["organization_id", "workspace_id", "dataset"],
        "azure": ["storage_account_name"],
    }
)
def upload(
    context: Any,
    blob_client: BlobServiceClient,
    org_id: str,
    work_id: str,
    dataset_id: str,
    folder: Optional[Path] = None,
) -> CommandResponse:
    """
    Upload csv files to blob storage container
    """
    api_storage = AzureStorageContainerService(blob_client=blob_client)
    api_storage.upload(
        org_id=org_id,
        work_id=work_id,
        dataset_id=dataset_id,
        context=context,
        folder=folder,
    )
    return CommandResponse.success()
