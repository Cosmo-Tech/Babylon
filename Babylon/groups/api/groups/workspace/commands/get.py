import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from cosmotech_api.api.workspace_api import WorkspaceApi
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.exceptions import ServiceException

from ......utils.api import convert_keys_case
from ......utils.api import filter_api_response_item
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.typing import QueryType

logger = getLogger("Babylon")

pass_workspace_api = make_pass_decorator(WorkspaceApi)


@command()
@describe_dry_run("Would call **workspace_api.find_workspace_by_id**")
@pass_workspace_api
@timing_decorator
@argument("workspace-id", required=False, type=QueryType())
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
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
@option(
    "-i",
    "--workspace-file",
    "workspace_file",
    help="In case the workspace id is retrieved from a file",
)
def get(
    workspace_api: WorkspaceApi,
    organization_id: str,
    fields: Optional[str] = None,
    output_file: Optional[str] = None,
    workspace_id: Optional[str] = None,
    workspace_file: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
):
    """Get the state of the workspace in the API."""

    if not workspace_id:
        if not workspace_file:
            logger.error("No id passed as argument or option use -d option"
                         " to pass an json or yaml file containing an workspace id.")
            return

        converted_workspace_content = get_api_file(
            api_file_path=workspace_file,
            use_working_dir_file=use_working_dir_file,
            logger=logger,
        )
        if not converted_workspace_content:
            logger.error("Error : can not get Workspace definition, please check your file")
            return

        try:
            workspace_id = converted_workspace_content["id"]
        except KeyError:
            try:
                workspace_id = converted_workspace_content["workspace_id"]
            except KeyError:
                logger.error("Can not get solution id, please check your file")
                return

    try:
        retrieved_workspace = workspace_api.find_workspace_by_id(workspace_id=workspace_id,
                                                                 organization_id=organization_id)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except ServiceException:
        logger.error(f"Organization with id : {organization_id} not found.")
        return
    except NotFoundException:
        logger.error(f"Workspace {workspace_id} not found in organization {organization_id}")
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
    logger.info(f"Workspace {workspace_id} detail was dumped on {output_file}")
    logger.debug(pformat(retrieved_workspace))