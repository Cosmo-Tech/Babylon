import json
import os
import pathlib
from logging import getLogger
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.mgmt.eventhub import EventHubManagementClient
from azure.mgmt.eventhub.models import AuthorizationRule

from click import argument
from click import command
from click import option
from click import Path

from ....utils.decorators import timing_decorator
from ....utils.typing import QueryType
from ....utils.response import CommandResponse
from ....utils.decorators import output_to_file
from ....utils.decorators import require_platform_key
from ....utils.decorators import require_deployment_key
from ....utils.environment import Environment
from ....utils.credentials import pass_azure_token
from ....utils.request import oauth_request
from ....utils.yaml_utils import yaml_to_json

logger = getLogger("Babylon")


@command()
@pass_azure_token("csm_api")
@require_platform_key("api_url")
@require_deployment_key("organization_id")
@require_deployment_key("workspace_id")
@option("-i", "--file", "file_name", type=QueryType())
def setkey(
    azure_token: str,
    api_url: str,
    organization_id: str,
    workspace_id: str,
    file_name: Optional[pathlib.Path],
) -> CommandResponse:

    env = Environment()
    file_name = file_name or env.working_dir.payload_path / "api/send_key.yaml"
    details = env.fill_template(file_name)
    details_json = yaml_to_json(details)
    response = oauth_request(f"{api_url}/organizations/{organization_id}/workspaces/{workspace_id}/secret",
                             azure_token,
                             type="POST",
                             data=details_json)
    if response is None:
        return CommandResponse.fail()
    logger.info(f"Successfully set sas key in workspace {workspace_id}")
    return CommandResponse.success()
