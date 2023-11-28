import pathlib

from logging import getLogger
from typing import Any
from click import command
from click import option
from click import argument
from click import Path
from azure.storage.blob import BlobServiceClient
from Babylon.utils.clients import pass_blob_client
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment

logger = getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_blob_client
@timing_decorator
@option(
    "--run-template",
    "run_template_id",
    help="The run Template identifier name example: 'Sensitive analysis'",
    type=QueryType(),
    required=True,
)
@option("--override", "override", is_flag=True, help="Override handler solution")
@argument("handler_id", type=QueryType())
@argument("handler_path", type=Path(path_type=pathlib.Path, exists=True))
@inject_context_with_resource({'api': ['url', 'organization_id', 'solution_id']})
def upload(context: Any,
           blob_client: BlobServiceClient,
           handler_path: pathlib.Path,
           handler_id: str,
           run_template_id: str,
           override: bool = False) -> CommandResponse:
    """Upload a solution handler zip to the solution"""
    org_id = context['api_organization_id']
    sol_id = context['api_solution_id']
    if not handler_path.suffix == ".zip":
        logger.error("solution handler upload only supports zip files")
        return CommandResponse.fail()
    check = blob_client.get_container_client(container=org_id)
    if not check.exists():
        logger.info(f"Container '{org_id}' not found")
        return CommandResponse.fail()
    client = blob_client.get_blob_client(container=org_id, blob=f"{sol_id}/{run_template_id}/{handler_id}.zip")
    if override and client.exists():
        client.delete_blob()
    with open(handler_path, "rb") as data:
        client.upload_blob(data)
    logger.info(f"Successfully sent handler file to solution {context['api_solution_id']}")
    return CommandResponse.success()
