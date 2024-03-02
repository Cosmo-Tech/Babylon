import logging

from typing import Any
from azure.mgmt.resource import ResourceManagementClient
from click import argument, option
from click import command
from Babylon.commands.azure.func.services.api import AzureAppFunctionService

from Babylon.utils.environment import Environment
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_arm_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_arm_client
@option(
    "--complete-mode",
    "deploy_mode_complete",
    is_flag=True,
    help="Flag to run on complete mode",
)
@argument("deployment_name", type=str)
@retrieve_state
def deploy(
    state: Any,
    arm_client: ResourceManagementClient,
    deployment_name: str,
    deploy_mode_complete: bool,
) -> CommandResponse:
    """
    Deploy a new function Scenario Donwload
    """
    service_state = state['services']
    service = AzureAppFunctionService(arm_client=arm_client, state=service_state)
    service.deploy(
        deployment_name=deployment_name,
        deploy_mode_complete=deploy_mode_complete,
    )
    return CommandResponse.success()
