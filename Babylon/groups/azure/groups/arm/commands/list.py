import logging
from pprint import pformat

from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from click import command
from click import make_pass_decorator

from ......utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")

pass_arm_client = make_pass_decorator(ResourceManagementClient)


@command()
@pass_arm_client
@require_platform_key("resource_group_name", "resource_group_name")
def list(
    arm_client: ResourceManagementClient,
    resource_group_name: str,
):
    """List all the deployments for a resource group."""

    try:
        deployment_list = arm_client.deployments.list_by_resource_group(resource_group_name)
    except HttpResponseError as _e:
        logger.error(f"An error occurred : {_e.message}")
        return

    deployments = [{
        'name': _ele.as_dict()['name'],
        'provisioning_state': _ele.as_dict()['properties']['provisioning_state'],
    } for _ele in deployment_list]

    logger.debug(deployment_list)
    logger.info(pformat(deployments))
    logger.info(f"Found {len(deployments)} deployments")
