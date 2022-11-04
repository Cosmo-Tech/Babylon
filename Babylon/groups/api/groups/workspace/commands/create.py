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

from ......utils import TEMPLATE_FOLDER_PATH
from ......utils.api import convert_keys_case
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import describe_dry_run
from ......utils.decorators import pass_environment
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.environment import Environment
from cosmotech_api.exceptions import ServiceException

logger = getLogger("Babylon")

pass_workspace_api = make_pass_decorator(WorkspaceApi)


@command()
@describe_dry_run("Would call **workspace_api.create_workspace** to register a new Workspace")
@timing_decorator
@pass_workspace_api
@pass_environment
@argument("workspace-name")
@require_deployment_key("send_scenario_metadata_to_event_hub")
@require_deployment_key("use_dedicated_event_hub_namespace")
@require_deployment_key("organization_id")
@require_deployment_key("solution_id")
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
    help="Your custom workspace definition file path",
)
@option(
    "-d",
    "--description",
    "workspace_description",
    help="Workspace description",
)
@option(
    "-o",
    "--output-file",
    "output_file",
    help="The path to the file where the created workspace should be outputted (json-formatted)",
    type=Path(),
)
@option(
    "-s",
    "--select",
    "select",
    type=bool,
    help="Select this new Workspace as babylon context workspace ?",
    default=True,
)
def create(
    env: Environment,
    workspace_api: WorkspaceApi,
    select: bool,
    solution_id: str,
    organization_id: str,
    workspace_name: str,
    use_dedicated_event_hub_namespace: str,
    send_scenario_metadata_to_event_hub: str,
    output_file: Optional[str] = None,
    workspace_file: Optional[str] = None,
    workspace_description: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
) -> Optional[str]:
    """Send a JSON or YAML file to the API to create a workspace."""

    converted_workspace_content = get_api_file(
        api_file_path=workspace_file
        if workspace_file else f"{TEMPLATE_FOLDER_PATH}/working_dir_template/API/Workspace.yaml",
        use_working_dir_file=use_working_dir_file if workspace_file else False,
        logger=logger,
    )
    if not converted_workspace_content:
        logger.error("Can not get correct workspace definition, please check your Workspace.YAML file")
        return

    if not workspace_description and "workspace_description" not in converted_workspace_content:
        converted_workspace_content["description"] = workspace_name

    converted_workspace_content["name"] = workspace_name
    converted_workspace_content["key"] = workspace_name.replace(" ", "")
    converted_workspace_content["send_scenario_metadata_to_event_hub"] = send_scenario_metadata_to_event_hub
    converted_workspace_content["use_dedicated_event_hub_namespace"] = use_dedicated_event_hub_namespace
    converted_workspace_content["solution"]["solution_id"] = solution_id

    if converted_workspace_content.get("id"):
        del converted_workspace_content["id"]
    if converted_workspace_content.get("workspace_id"):
        del converted_workspace_content["workspace_id"]

    logger.info(f"Creating Workspace {workspace_name}")

    try:
        retrieved_workspace = workspace_api.create_workspace(organization_id=organization_id,
                                                             workspace=converted_workspace_content)
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except ServiceException:
        logger.error(f"Organization {organization_id} or Solution {solution_id} not found.")
        return
    except NotFoundException:
        logger.error(f"Organization {organization_id} or Solution {solution_id} not found.")
        return

    if select:
        env.configuration.set_deploy_var("workspace_id", retrieved_workspace["id"])
        env.configuration.set_deploy_var("workspace_key", retrieved_workspace["key"])

    logger.info(
        "Created new workspace with \n"
        f" - id: {retrieved_workspace['id']}\n"
        f" - key: {retrieved_workspace['key']}\n"
        f" - send_scenario_metadata_to_event_hub: {retrieved_workspace['send_scenario_metadata_to_event_hub']}\n"
        f" - use_dedicated_event_hub_namespace: {retrieved_workspace['use_dedicated_event_hub_namespace']}")
    logger.debug(pformat(retrieved_workspace))

    if output_file:
        converted_content = convert_keys_case(retrieved_workspace, underscore_to_camel)
        with open(output_file, "w") as _f:
            try:
                json.dump(converted_content, _f, ensure_ascii=False)
            except TypeError:
                json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
        logger.info(f"Content was dumped on {output_file}")

    return retrieved_workspace['id']
