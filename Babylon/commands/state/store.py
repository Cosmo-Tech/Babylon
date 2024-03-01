import glob
import logging
import os
import shutil
import uuid

from pathlib import Path
from typing import Any
from zipfile import ZipFile
from posixpath import basename
from click import command, option
from azure.storage.blob import BlobServiceClient
from Babylon.utils.clients import pass_blob_client
from Babylon.utils.decorators import injectcontext
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_blob_client
@option("--id", "id")
@inject_context_with_resource({"api": ["workspace_key"]})
def store(context: Any, blob_client: BlobServiceClient, id: str) -> CommandResponse:
    """
    Save state in storage account
    """
    if not Path(".state").exists():
        os.mkdir(".state")
    works_key = context['api_workspace_key']
    config_zip = env.working_dir.path / ".state" / f"{env.context_id}.{env.environ_id}.zip"
    config = env.working_dir.path / "config"
    schema = str(config / f"{env.context_id}.{env.environ_id}.*.yaml")
    files = glob.glob(schema)
    with ZipFile(config_zip, 'w') as zip_object:
        for item in files:
            zip_object.write(item, basename(item))
    check = blob_client.get_container_client(container="babylon-state")
    if not check.exists():
        logger.info("Container babylon-state not found")
        return CommandResponse.fail()
    guid = id or uuid.uuid4()
    client = blob_client.get_blob_client(container="babylon-state", blob=f"{guid}/{works_key}.{basename(config_zip)}")
    if client.exists():
        client.delete_blob()
    with open(config_zip, "rb") as data:
        client.upload_blob(data)
    logger.info(f"Successfully saved: {guid}")
    shutil.rmtree(".state")
    return CommandResponse.success()
