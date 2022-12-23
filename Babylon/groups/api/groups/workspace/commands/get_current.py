import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.workspace_api import WorkspaceApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.exceptions import ServiceException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response_item
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse

logger = getLogger("Babylon")

pass_workspace_api = make_pass_decorator(WorkspaceApi)


@command()
@describe_dry_run("Would call **workspace_api.find_workspace_by_id**")
@pass_workspace_api
@timing_decorator
@require_deployment_key("workspace_id", "workspace_id")
@require_deployment_key("organization_id", "organization_id")
@option(
    "-o",
    "--output-file",
    "output_file",
    help="The path to the file where Workspace details should be outputted (json-formatted)",
    type=Path(),
)
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
)
def get_current(
    workspace_api: WorkspaceApi,
    workspace_id: str,
    organization_id: str,
    fields: Optional[str] = None,
    output_file: Optional[str] = None,
) -> CommandResponse:
    """Get the state of the workspace in the API."""

    try:
        retrieved_workspace = workspace_api.find_workspace_by_id(workspace_id=workspace_id,
                                                                 organization_id=organization_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id : {organization_id} not found.")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Workspace {workspace_id} not found in organization {organization_id}")
        return CommandResponse.fail()

    if fields:
        retrieved_workspace = filter_api_response_item(retrieved_workspace, fields.split(","))
    if not output_file:
        logger.info(f"Workspace {workspace_id} details :")
        logger.info(pformat(retrieved_workspace))
        return CommandResponse.fail()

    converted_content = convert_keys_case(retrieved_workspace, underscore_to_camel)
    with open(output_file, "w") as _f:
        try:
            json.dump(converted_content, _f, ensure_ascii=False)
        except TypeError:
            json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
    logger.info(f"Dataset {workspace_id} detail was dumped on {output_file}")
    logger.debug(pformat(retrieved_workspace))
    return CommandResponse(data=retrieved_workspace)
