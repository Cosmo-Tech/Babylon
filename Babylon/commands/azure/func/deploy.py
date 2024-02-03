import logging
import pathlib

from typing import Any, Optional
from azure.mgmt.resource import ResourceManagementClient
from click import Path, argument, option
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
@option(
    "--file",
    "deploy_file",
    type=Path(readable=True, dir_okay=False, path_type=pathlib.Path),
    help="Your custom arm description file yaml",
)
@argument("deployment_name", type=QueryType())
@inject_context_with_resource(
    {"api": ["organization_id", "workspace_key"], "azure": ["resource_group_name"]}
)
def deploy(
    context: Any,
    arm_client: ResourceManagementClient,
    deployment_name: str,
    deploy_file: Optional[Path],
    deploy_mode_complete: bool,
) -> CommandResponse:
    """
    Deploy a new function Scenario Donwload
    """
    apiFunc = AzureAppFunctionService()
    apiFunc.deploy(
        deployment_name=deployment_name,
        deploy_mode_complete=deploy_mode_complete,
        arm_client=arm_client,
    )
    return CommandResponse.success()
