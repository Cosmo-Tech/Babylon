import os
import logging
import shutil
import zipfile

from pathlib import Path
from typing import Any
from click import argument, command
from azure.storage.blob import BlobServiceClient
from Babylon.utils.clients import pass_blob_client
from Babylon.utils.decorators import wrapcontext
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.environment import Environment
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_blob_client
@argument("id", type=QueryType())
@inject_context_with_resource({"api": ["workspace_key"]})
def get(context: Any, blob_client: BlobServiceClient, id: str) -> CommandResponse:
    """
    Retrieve state from storage account
    """
    if not Path(".state").exists():
        os.mkdir(".state")
    works_key = context['api_workspace_key']
    config_zip = f"{id}/{works_key}.{env.context_id}.{env.environ_id}.zip"
    check = blob_client.get_container_client(container="babylon-state")
    if not check.exists():
        logger.info("Container babylon-state not found")
        return CommandResponse.fail()
    data = check.download_blob(config_zip).readall()
    with open(file=f".state/{env.context_id}.{env.environ_id}.zip", mode="wb") as download_file:
        download_file.write(data)
    with zipfile.ZipFile(f".state/{env.context_id}.{env.environ_id}.zip") as zip_file:
        zip_file.extractall("config")
    logger.info(f"Successfully retrieved: {id}")
    shutil.rmtree(".state")
    return CommandResponse.success()
