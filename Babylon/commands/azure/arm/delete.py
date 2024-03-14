import logging

from typing import Any, Optional
from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from click import argument
from click import command
from click import option
from Babylon.utils.decorators import retrieve_state, injectcontext
from Babylon.utils.interactive import confirm_deletion
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_arm_client

from Babylon.utils.environment import Environment

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@injectcontext()
@pass_arm_client
@option("-D", "force_validation", is_flag=True, help="Force Delete")
@argument("deployment_name", type=str)
@retrieve_state
def delete(
    state: Any,
    arm_client: ResourceManagementClient,
    deployment_name: str,
    force_validation: Optional[bool] = False,
) -> CommandResponse:
    """
    Delete a resource deployment via arm deployment
    """
    resource_group_name = state["services"]["azure"]["resource_group_name"]
    if not force_validation and not confirm_deletion("azure deployment", deployment_name):
        return CommandResponse.fail()
    logger.info(f"Deleting resource deployment {deployment_name} ...")
    try:
        poller = arm_client.deployments.begin_delete(
            resource_group_name=resource_group_name,
            deployment_name=deployment_name,
        )
    except HttpResponseError as _e:
        logger.error(f"An error occurred : {_e.message}")
        return CommandResponse.fail()
    logger.debug(poller.result())
    logger.info(f"Deployment {deployment_name} deleted with status : {poller.status()}")
    return CommandResponse.success({"status": poller.status()})
