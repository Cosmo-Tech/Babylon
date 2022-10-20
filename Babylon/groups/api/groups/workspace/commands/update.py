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

from ......utils.api import get_api_file
from ......utils.decorators import allow_dry_run
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator

logger = getLogger("Babylon")

pass_workspace_api = make_pass_decorator(WorkspaceApi)


@command()
@allow_dry_run
@timing_decorator
@pass_workspace_api
@argument("workspace_file")
@require_deployment_key("sendScenarioMetadataToEventHub", "send_scenario_metadata_to_event_hub")
@require_deployment_key("useDedicatedEventHubNamespace", "use_dedicated_event_hub_namespace")
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
def update(
    workspace_api: WorkspaceApi,
    workspace_file: str,
    send_scenario_metadata_to_event_hub: str,
    use_dedicated_event_hub_namespace: str,
    solution_id: str,
    organization_id: str,
    use_working_dir_file: Optional[bool] = False,
    dry_run: bool = False,
):
    """Send a JSON or YAML file to the API to update a workspace."""

    if dry_run:
        logger.info("DRY RUN - Would call workspace_api.create_workspace")
        return

    converted_workspace_content = get_api_file(
        api_file_path=workspace_file,
        use_working_dir_file=use_working_dir_file,
        logger=logger,
    )
    if not converted_workspace_content:
        logger.error("Error : can not get correct connector definition, please check your Workspace.YAML file")
        return

    converted_workspace_content["sendScenarioMetadataToEventHub"] = send_scenario_metadata_to_event_hub
    converted_workspace_content["useDedicatedEventHubNamespace"] = use_dedicated_event_hub_namespace
    converted_workspace_content["solution"]["solution_id"] = solution_id

    if "id" not in converted_workspace_content:
        logger.error("Error : can not get connector id in the Connector.YAML file")
        return

    workspace_id = converted_workspace_content["id"]
    del converted_workspace_content["id"]

    try:
        retrieved_workspace = workspace_api.update_workspace(
            workspace_id=workspace_id, organization_id=organization_id, workspace=converted_workspace_content
        )
    except UnauthorizedException:
        logger.error("Unauthorized access to the cosmotech api")
        return
    except NotFoundException:
        logger.error(f"Workspace {workspace_id} does not exists in organization {organization_id}.")
        return

    logger.debug(pformat(retrieved_workspace))
    logger.info(f"Workspace: {retrieved_workspace['id']} updated.")
