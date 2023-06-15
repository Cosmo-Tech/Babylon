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


@command(name="create-key")
@require_platform_key("resource_group_name")
@require_platform_key("azure_subscription")
@require_deployment_key("organization_id")
@require_deployment_key("workspace_key")
def create_key(
    azure_subscription: str,
    organization_id: str,
    workspace_key: str,
    resource_group_name: str,
) -> CommandResponse:

    client = EventHubManagementClient(credential=DefaultAzureCredential(), subscription_id=azure_subscription)
    sas = client.namespaces.create_or_update_authorization_rule(
        resource_group_name=resource_group_name,
        authorization_rule_name="cosmosas",
        namespace_name=f"{organization_id.lower()}-{workspace_key.lower()}",
        parameters=AuthorizationRule(
            rights=["Manage", "Listen", "Send"]
        )
    )
    if sas is None:
        return CommandResponse.fail()
    logger.info(f"Successfully create key in namspaces")
    return CommandResponse.success()
