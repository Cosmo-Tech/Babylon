import json
import logging
import pathlib
from typing import Optional

from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from azure.mgmt.resource.resources.models import Deployment
from azure.mgmt.resource.resources.models import DeploymentProperties
from azure.mgmt.resource.resources.models import DeploymentPropertiesExtended
from azure.mgmt.resource.resources.models import DeploymentExtended
from click import Path, argument, option
from click import command
from Babylon.utils.interactive import confirm_deploy_arm_mode

from Babylon.utils.typing import QueryType

from ....utils.environment import Environment
from ....utils.decorators import require_deployment_key
from ....utils.response import CommandResponse
from ....utils.clients import pass_arm_client

logger = logging.getLogger("Babylon")


@command(name="runtmp")
@pass_arm_client
@require_deployment_key("resource_group_name")
@require_deployment_key("organization_id")
@require_deployment_key("workspace_key")
@argument("deployment_name", type=QueryType(), default="armdeployment")
@option("-f", "--file", "deploy_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@option("--complete-mode", "deploy_mode_complete", is_flag=True)
def run_template(arm_client: ResourceManagementClient,
        organization_id: str,
        workspace_key: str,
        resource_group_name: str,
        deployment_name: str,
        deploy_file: Optional[Path],
        deploy_mode_complete: bool = False,
    ) -> CommandResponse:
    """Apply a resource deployment config via arm template file in working directory."""
    mode = DeploymentMode.INCREMENTAL
    if deploy_mode_complete:
        logger.warn("Warning: In complete mode, Resource Manager deletes resources that exist in the resource group but aren't specified in the template.")
        if confirm_deploy_arm_mode():
            mode = DeploymentMode.COMPLETE

    env = Environment()

    if not deploy_file:
        logger.error("Deploy file not found")
        return CommandResponse.fail()
        
    arm_template = env.fill_template(deploy_file, data={
        "instance_name": f"{organization_id.lower()}-{workspace_key.lower()}",
        "organization_id": organization_id.lower(),
        "workspace_key": workspace_key.lower()
    })
    arm_template = json.loads(arm_template)
    parameters = {k: { "value": v['defaultValue'] } for k, v in dict(arm_template["parameters"]).items()}
    logger.info(f"Starting deployment")

    try:
        poller = arm_client.deployments.begin_create_or_update(
            resource_group_name=resource_group_name,
            deployment_name=deployment_name,
            parameters=Deployment(
                properties=DeploymentProperties(
                    mode=DeploymentMode.INCREMENTAL,
                    template=arm_template,
                    parameters=parameters
                )
            ),
        )
        poller.wait()
        # check if done
        if not poller.done():
            return CommandResponse.fail()
        # deployments created

    except HttpResponseError as _e:
        logger.error(f"An error occurred : {_e.message}")
        return CommandResponse.fail()

    _ret: list[str] = [f"Provisioning state: successful"]
    logger.info("\n".join(_ret))
    return CommandResponse.success()
