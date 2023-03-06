import logging
from typing import Optional

from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from click import argument
from click import command
from click import option

from ....utils.decorators import require_deployment_key
from ....utils.decorators import timing_decorator
from ....utils.interactive import confirm_deletion
from ....utils.response import CommandResponse
from ....utils.clients import pass_arm_client

logger = logging.getLogger("Babylon")


@command()
@pass_arm_client
@argument("deployment_name")
@require_deployment_key("resource_group_name", "resource_group_name")
@option(
    "-f",
    "--force",
    "force_validation",
    is_flag=True,
    help="Don't ask for validation before delete",
)
@timing_decorator
def delete(
    arm_client: ResourceManagementClient,
    deployment_name: str,
    resource_group_name: str,
    force_validation: Optional[bool] = False,
) -> CommandResponse:
    """Delete a resource deployment via arm deployment."""

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
