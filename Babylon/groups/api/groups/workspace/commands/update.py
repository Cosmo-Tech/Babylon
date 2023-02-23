import json
from logging import getLogger
from pprint import pformat
from typing import Optional

from click import Path
from click import command
from click import option
from cosmotech_api.api.workspace_api import WorkspaceApi
from cosmotech_api.exceptions import ForbiddenException
from cosmotech_api.exceptions import NotFoundException
from cosmotech_api.exceptions import ServiceException
from cosmotech_api.exceptions import UnauthorizedException
from cosmotech_api.api_client import ApiClient

from ......utils.api import convert_keys_case
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.environment import Environment
from ......utils.response import CommandResponse
from ......utils.clients import pass_api_client

logger = getLogger("Babylon")


@command()
@describe_dry_run("Would call **workspace_api.create_workspace**")
@timing_decorator
@pass_api_client
@option(
    "-i",
    "--workspace-file",
    "workspace_file",
    help="In case the workspace id is retrieved from a file",
)
@option(
    "-o",
    "--output-file",
    "output_file",
    help="The path to the file where new Workspace details should be outputted (json-formatted)",
    type=Path(),
)
@require_deployment_key("use_dedicated_event_hub_namespace", "send_scenario_metadata_to_event_hub")
@require_deployment_key("use_dedicated_event_hub_namespace", "use_dedicated_event_hub_namespace")
@require_deployment_key("organization_id", "organization_id")
@require_deployment_key("solution_id", "solution_id")
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    help="Should the path be relative to the working directory ?",
)
def update(
    api_client: ApiClient,
    solution_id: str,
    workspace_file: str,
    organization_id: str,
    use_dedicated_event_hub_namespace: str,
    send_scenario_metadata_to_event_hub: str,
    output_file: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
) -> CommandResponse:
    """Send a JSON or YAML file to the API to update a workspace."""
    workspace_api = WorkspaceApi(api_client)
    env = Environment()
    converted_workspace_content = get_api_file(api_file_path=workspace_file, use_working_dir_file=use_working_dir_file)
    if not converted_workspace_content:
        logger.error("Error : can not get correct connector definition, please check your Workspace.YAML file")
        return CommandResponse.fail()

    converted_workspace_content["send_scenario_metadata_to_event_hub"] = send_scenario_metadata_to_event_hub
    converted_workspace_content["use_dedicated_event_hub_namespace"] = use_dedicated_event_hub_namespace
    converted_workspace_content["solution"]["solution_id"] = solution_id

    if "id" not in converted_workspace_content:
        logger.error("Error : can not get connector id in the Connector.YAML file")
        return CommandResponse.fail()

    workspace_id = converted_workspace_content["id"]
    del converted_workspace_content["id"]

    try:
        retrieved_workspace = workspace_api.update_workspace(workspace_id=workspace_id,
                                                             organization_id=organization_id,
                                                             workspace=converted_workspace_content)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return CommandResponse.fail()
    except ServiceException:
        logger.error(f"Organization with id : {organization_id} not found.")
        return CommandResponse.fail()
    except NotFoundException:
        logger.error(f"Workspace {workspace_id} not found in organization {organization_id}")
        return CommandResponse.fail()
    except ForbiddenException:
        logger.error(f"You are not allowed to update the workspace : {workspace_id}")
        return CommandResponse.fail()

    env.configuration.set_deploy_var("workspace_key", retrieved_workspace["key"])

    if output_file:
        converted_content = convert_keys_case(retrieved_workspace, underscore_to_camel)
        with open(output_file, "w") as _f:
            try:
                json.dump(converted_content, _f, ensure_ascii=False)
            except TypeError:
                json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
        logger.info(f"Content was dumped on {output_file}")

    logger.debug(pformat(retrieved_workspace))
    logger.info(f"Workspace: {retrieved_workspace['id']} updated.")
    return CommandResponse.success(retrieved_workspace)
