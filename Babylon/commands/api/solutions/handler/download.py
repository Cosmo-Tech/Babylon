import os
import zipfile

from posixpath import basename
from logging import getLogger
from typing import Any
from click import command
from click import option
from click import argument
from azure.storage.blob import BlobServiceClient
from Babylon.utils.clients import pass_blob_client
from Babylon.utils.decorators import inject_context_with_resource, timing_decorator, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import output_to_file

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_blob_client
@timing_decorator
@output_to_file
@option("--organization-id", "org_id", type=QueryType(), help="Organization id or referenced in configuration")
@option("--solution-id", "sol_id", type=QueryType(), help="Solution id or referenced in configuration")
@option("--run-template", "run_template_id", help="The run Template identifier", required=True, type=QueryType())
@argument("handler_id", type=QueryType())
@inject_context_with_resource({'api': ['url', 'organization_id', "solution_id"]})
def download(blob_client: BlobServiceClient, context: Any, org_id: str, sol_id: str, handler_id: str,
             run_template_id: str) -> CommandResponse:
    """Download a solution handler zip from the solution"""
    org_id = context['api_organization_id']
    sol_id = context['api_solution_id']
    check = blob_client.get_container_client(container=org_id)
    if not check.exists():
        logger.info(f"Container '{org_id}' not found")
        return CommandResponse.fail()
    client = blob_client.get_blob_client(container=org_id, blob=f"{sol_id}/{run_template_id}/{handler_id}.zip")
    data = client.download_blob().readall()
    zf = zipfile.ZipFile("data.zip", mode='w', compression=zipfile.ZIP_DEFLATED)
    zf.writestr(basename(client.blob_name), data)
    zf.extractall(".")
    os.remove("data.zip")
    logger.info("Successfully download handler file")
    return CommandResponse.success()
