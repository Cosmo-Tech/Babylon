import json
import logging
import pathlib

from typing import Any
from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from azure.mgmt.resource.resources.models import Deployment
from azure.mgmt.resource.resources.models import DeploymentProperties
from click import argument, option
from click import command
from Babylon.utils.interactive import confirm_deploy_arm_mode
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource, wrapcontext
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_arm_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@wrapcontext
@pass_arm_client
@argument("deployment_name", type=QueryType())
@option("--file", "deploy_file", type=str)
@option("--complete-mode", "deploy_mode_complete", is_flag=True)
@inject_context_with_resource({'api': ['organization_id', 'workspace_key'], 'azure': ['resource_group_name']})
def run(
    context: Any,
    arm_client: ResourceManagementClient,
    deployment_name: str,
    deploy_file: str,
    deploy_mode_complete: bool = False,
) -> CommandResponse:
    """
    Apply a resource deployment config via arm template file in working directory
    """
    organization_id = context['api_organization_id']
    workspace_key = context['api_workspace_key']
    resource_group_name = context['azure_resource_group_name']

    deploy_file = pathlib.Path(env.convert_template_path(deploy_file)) or pathlib.Path(deploy_file)
    mode = DeploymentMode.INCREMENTAL
    if deploy_mode_complete:
        logger.warn("""Warning: In complete mode\n
                    Resource Manager deletes resources that exist in the resource group,\n
                    but aren't specified in the template.""")
        if confirm_deploy_arm_mode():
            mode = DeploymentMode.COMPLETE

    if not deploy_file:
        logger.error("Deploy file not found")
        return CommandResponse.fail()

    arm_template = env.fill_template(deploy_file,
                                     data={
                                         "instance_name": f"{organization_id.lower()}-{workspace_key.lower()}",
                                         "organization_id": organization_id.lower(),
                                         "workspace_key": workspace_key.lower()
                                     })
    arm_template = json.loads(arm_template)
    parameters = {k: {"value": v['defaultValue']} for k, v in dict(arm_template["parameters"]).items()}
    logger.info("Starting deployment")

    try:
        poller = arm_client.deployments.begin_create_or_update(
            resource_group_name=resource_group_name,
            deployment_name=deployment_name,
            parameters=Deployment(
                properties=DeploymentProperties(mode=mode, template=arm_template, parameters=parameters)),
        )
        poller.wait()
        if not poller.done():
            return CommandResponse.fail()

    except HttpResponseError as _e:
        logger.error(f"An error occurred : {_e.message}")
        return CommandResponse.fail()

    logger.info("Provisioning state: successful")
    return CommandResponse.success()
