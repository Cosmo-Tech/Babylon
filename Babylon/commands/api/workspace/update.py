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

from ....utils.decorators import describe_dry_run
from ....utils.decorators import require_deployment_key
from ....utils.decorators import timing_decorator
from ....utils.environment import Environment
from ....utils.response import CommandResponse
from ....utils.clients import pass_api_client

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
    return CommandResponse.success()
