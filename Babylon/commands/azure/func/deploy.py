import logging

from typing import Any
from azure.mgmt.resource import ResourceManagementClient
from click import argument, option
from click import command
from Babylon.commands.azure.func.service.api import AzureAppFunctionService
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_arm_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext()
@pass_arm_client
@option(
    "--complete-mode",
    "deploy_mode_complete",
    is_flag=True,
    help="Flag to run on complete mode",
)
@argument("deployment_name", type=QueryType())
@inject_context_with_resource(
    {"api": ["organization_id", "workspace_key"], "azure": ["resource_group_name"]}
)
def deploy(
    context: Any,
    arm_client: ResourceManagementClient,
    deployment_name: str,
    deploy_mode_complete: bool,
) -> CommandResponse:
    """
    Deploy a new function Scenario Donwload
    """
    service = AzureAppFunctionService(arm_client=arm_client, state=context)
    service.deploy(
        deployment_name=deployment_name,
        deploy_mode_complete=deploy_mode_complete,
    )
    return CommandResponse.success()
