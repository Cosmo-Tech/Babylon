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
from ......utils.decorators import allow_dry_run
from ......utils.decorators import pass_environment
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.environment import Environment

logger = getLogger("Babylon")

pass_workspace_api = make_pass_decorator(WorkspaceApi)


@command()
@allow_dry_run
@timing_decorator
@pass_workspace_api
@pass_environment
@argument("workspace_file", required=False)
@require_deployment_key("send_scenario_metadata_to_event_hub", "send_scenario_metadata_to_event_hub")
@require_deployment_key("use_dedicated_event_hub_namespace", "use_dedicated_event_hub_namespace")
@require_deployment_key("organization_id", "organization_id")
@require_deployment_key("solution_id", "solution_id")
@option(
    "-e",
    "--use-working-dir-file",
    "use_working_dir_file",
    is_flag=True,
    type=bool,
    help="Should the path be relative to the working directory ?",
)
@option(
    "-n",
    "--name",
    "workspace_name",
    required=True,
    help="New workspace name",
)
@option(
    "-d",
    "--description",
    "workspace_description",
    help="New workspace description",
)
@option(
    "-o",
    "--output-file",
    "output_file",
    help="File to which content should be outputted (json-formatted)",
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
    organization_id: str,
    workspace_name: str,
    send_scenario_metadata_to_event_hub: str,
    use_dedicated_event_hub_namespace: str,
    solution_id: str,
    select: bool,
    workspace_file: Optional[str] = None,
    output_file: Optional[str] = None,
    workspace_description: Optional[str] = None,
    use_working_dir_file: Optional[bool] = False,
    dry_run: Optional[bool] = False,
):
    """Send a JSON or YAML file to the API to create a workspace."""

    if dry_run:
        logger.info("DRY RUN - Would call workspace_api.create_workspace")
        return

    converted_workspace_content = get_api_file(
        api_file_path=workspace_file
        if workspace_file
        else f"{TEMPLATE_FOLDER_PATH}/working_dir_template/API/Workspace.yaml",
        use_working_dir_file=use_working_dir_file if workspace_file else False,
        logger=logger,
    )
    if not converted_workspace_content:
        logger.error("Error : can not get correct workspace definition, please check your Workspace.YAML file")
        return

    if not workspace_description and "workspace_description" not in converted_workspace_content:
        converted_workspace_content["description"] = workspace_name

    converted_workspace_content["name"] = workspace_name
    converted_workspace_content["key"] = workspace_name.replace(" ", "")
    converted_workspace_content["sendScenarioMetadataToEventHub"] = send_scenario_metadata_to_event_hub
    converted_workspace_content["useDedicatedEventHubNamespace"] = use_dedicated_event_hub_namespace
    converted_workspace_content["solution"]["solution_id"] = solution_id

    try:
        retrieved_workspace = workspace_api.create_workspace(
            organization_id=organization_id, workspace=converted_workspace_content
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Organization with id {organization_id} does not exists.")
        return

    if select:
        env.configuration.set_deploy_var("workspace_id", retrieved_workspace["id"])

    logger.info(f"Created new workspace with id: {retrieved_workspace['id']}")
    logger.debug(pformat(retrieved_workspace))

    if output_file:
        converted_content = convert_keys_case(retrieved_workspace, underscore_to_camel)
        with open(output_file, "w") as _f:
            try:
                json.dump(converted_content, _f, ensure_ascii=False)
            except TypeError:
                json.dump(converted_content.to_dict(), _f, ensure_ascii=False)
        logger.info(f"Content was dumped on {output_file}")
