import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.workspace_api import WorkspaceApi
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse

logger = getLogger("Babylon")

pass_workspace_api = make_pass_decorator(WorkspaceApi)


@command()
@describe_dry_run("Would call **workspace_api.find_all_workspaces**")
@pass_workspace_api
@timing_decorator
@require_deployment_key("organization_id", "organization_id")
@option(
    "-o",
    "--output-file",
    "output_file",
    help="The path to the file where Workspaces should be outputted (json-formatted)",
    type=Path(),
)
@option(
    "-f",
    "--fields",
    "fields",
    help="Fields witch will be keep in response data, by default all",
)
def get_all(
    workspace_api: WorkspaceApi,
    organization_id: str,
    fields: Optional[str] = None,
    output_file: Optional[str] = None,
) -> CommandResponse:
    """Get all registered workspaces."""
    try:
        retrieved_workspaces = workspace_api.find_all_workspaces(organization_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api.")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id : {organization_id} not found.")
        return CommandResponse.fail()

    if fields:
        retrieved_workspaces = filter_api_response(retrieved_workspaces, fields.split(","))
    logger.info(f"Found {len(retrieved_workspaces)} workspaces")
    if not output_file:
        logger.info(pformat(retrieved_workspaces, sort_dicts=False))
        return CommandResponse.fail()

    _workspaces_to_dump = [convert_keys_case(_ele, underscore_to_camel) for _ele in retrieved_workspaces]
    with open(output_file, "w") as _file:
        try:
            json.dump(_workspaces_to_dump, _file, ensure_ascii=False)
        except TypeError:
            json.dump([_ele.to_dict() for _ele in _workspaces_to_dump], _file, ensure_ascii=False)
    logger.info("Full content was dumped on %s.", output_file)
    return CommandResponse.success({"workspaces": retrieved_workspaces})
