from typing import Any

from azure.mgmt.resource import ResourceManagementClient
from click import command

from Babylon.commands.azure.func.services.api import AzureAppFunctionService
from Babylon.utils.clients import pass_arm_client
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.response import CommandResponse


@command()
@injectcontext()
@pass_arm_client
@retrieve_state
def delete(
    state: Any,
    arm_client: ResourceManagementClient,
    azf_name: str,
) -> CommandResponse:
    """
    Deploy a new function Scenario Donwload
    """
    service_state = state["services"]
    service = AzureAppFunctionService(arm_client=arm_client, state=service_state)
    service.delete()
    return CommandResponse.success()
