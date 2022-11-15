import logging

from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from click import argument
from click import command
from click import make_pass_decorator

from ......utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")

pass_arm_client = make_pass_decorator(ResourceManagementClient)


@command()
@pass_arm_client
@argument("deployment_name")
@require_platform_key("resource_group_name", "resource_group_name")
def delete(
    arm_client: ResourceManagementClient,
    deployment_name: str,
    resource_group_name: str,
):
    """Command created from a template"""

    try:
        poller = arm_client.deployments.begin_delete(
            resource_group_name=resource_group_name,
            deployment_name=deployment_name,
        )
    except HttpResponseError as _e:
        logger.error(f"An error occurred : {_e.message}")
        return

    adt_creation_result = poller.result()
    logger.info(adt_creation_result)
