import logging

from typing import Any
from click import command
from click import argument, option
from Babylon.commands.azure.arm.services.api import ArmService
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.clients import pass_arm_client
from Babylon.utils.response import CommandResponse
from azure.mgmt.resource import ResourceManagementClient
from Babylon.utils.decorators import retrieve_state, injectcontext

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_arm_client
@argument("deployment_name", type=QueryType())
@option("--complete-mode", "deploy_mode_complete", is_flag=True, help="Mode deployment")
@retrieve_state
def run(
    state: Any,
    arm_client: ResourceManagementClient,
    deployment_name: str,
    deploy_mode_complete: bool = False,
) -> CommandResponse:
    """
    Apply a resource deployment config via arm template file in working directory
    """
    service_state = state["services"]
    service = ArmService(arm_client=arm_client, state=service_state)
    service.run(deployment_name=deployment_name, deploy_mode_complete=deploy_mode_complete)
    return CommandResponse.success()
