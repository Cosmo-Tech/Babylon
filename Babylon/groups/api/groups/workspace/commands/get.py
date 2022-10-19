import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.workspace_api import WorkspaceApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response_item
from ......utils.api import underscore_to_camel
from ......utils.decorators import allow_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_workspace_api = make_pass_decorator(WorkspaceApi)


@command()
@allow_dry_run
@pass_workspace_api
@timing_decorator
@argument("workspace_id", type=str)
@require_deployment_key("organization_id", "organization_id")
@option(
    "-o",
    "--output_file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
    type=str,
)
@option(
    "-f",
    "--fields",
    "fields",
    type=str,
    help="Fields witch will be keep in response data, by default all",
)
def get(
    workspace_api: WorkspaceApi,
    workspace_id: str,
    organization_id: str,
    output_file: Optional[str] = None,
    fields: str = None,
    dry_run: bool = False,
):
    """Get the state of the workspace in the API."""

    if dry_run:
        logger.info("DRY RUN - Would call workspace_api.find_workspace_by_id")
        return

    try:
        retrieved_workspace = workspace_api.find_workspace_by_id(workspace_id=workspace_id, organization_id=organization_id)
    except NotFoundException:
        logger.error(f"Workspace {workspace_id} does not exists in organization {organization_id}.")
        return
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return

    if fields:
        retrieved_workspace = filter_api_response_item(retrieved_workspace, fields.split(","))
    if not output_file:
        logger.info(f"Workspace {workspace_id} details :")
        logger.info(pformat(retrieved_workspace))
        return

    converted_content = convert_keys_case(retrieved_workspace, underscore_to_camel)
    with open(output_file, "w") as _f:
        try:
            json.dump(converted_content, _f, ensure_ascii=False)
        except TypeError:
            json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
    logger.info(f"Datset {workspace_id} detail was dumped on {output_file}")
    logger.debug(pformat(retrieved_workspace))
