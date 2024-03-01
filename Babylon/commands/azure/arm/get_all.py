import logging

from typing import Any
from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from click import command
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.decorators import timing_decorator
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_arm_client
from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@timing_decorator
@pass_arm_client
@retrieve_state
def get_all(
    state: Any,
    arm_client: ResourceManagementClient,
) -> CommandResponse:
    """
    Get all the deployments for a resource group
    """
    resource_group_name = state["azure"]["resource_group_name"]
    try:
        deployment_list = arm_client.deployments.list_by_resource_group(resource_group_name)
    except HttpResponseError as _e:
        logger.error(f"An error occurred : {_e.message}")
        return CommandResponse.fail()

    deployments = [{
        'name': _ele.as_dict()['name'],
        'provisioning_state': _ele.as_dict()['properties']['provisioning_state'],
    } for _ele in deployment_list]
    return CommandResponse.success(deployments, verbose=True)
