import os
import glob
import logging
import pathlib

from typing import Any, Optional
from azure.storage.blob import BlobServiceClient
from click import Path, command, option
from Babylon.utils.decorators import timing_decorator, wrapcontext
from Babylon.utils.clients import pass_blob_client
from Babylon.utils.response import CommandResponse
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@timing_decorator
@pass_blob_client
@option("--folder",
        "folder",
        required=True,
        type=Path(readable=True, dir_okay=True, exists=True, path_type=pathlib.Path),
        help="Folder with cvs files to upload")
@option("--org-id", "org_id", help="Organization id")
@option("--work-id", "work_id", help="Workspace id")
@inject_context_with_resource({'api': ['organization_id', 'workspace_id'], 'azure': ['storage_account_name']})
def upload(
    context: Any,
    blob_client: BlobServiceClient,
    org_id: str,
    work_id: str,
    folder: Optional[Path] = None,
) -> CommandResponse:
    """
    Upload csv files to blob storage container
    """
    organization_id = org_id or context['api_organization_id']
    workspace_id = work_id or context['api_workspace_id']
    files = glob.glob(os.path.join(folder, "*.csv"))
    check = blob_client.get_container_client(container=organization_id.lower())
    if not check.exists():
        logger.info(f"Container '{organization_id.lower()}' not found")
        return CommandResponse.fail()

    for f in files:
        client = blob_client.get_blob_client(container=organization_id.lower(),
                                             blob=f"{workspace_id.lower()}/datasets/{os.path.basename(f)}")
        _f: pathlib.Path = env.pwd / f
        with open(_f, "rb") as data:
            client.upload_blob(data)
    logger.info("Successfully uploaded")
    return CommandResponse.success()
