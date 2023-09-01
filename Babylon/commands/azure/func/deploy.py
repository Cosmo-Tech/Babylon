import json
import logging
import pathlib

from typing import Any, Optional
from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from azure.mgmt.resource.resources.models import Deployment
from azure.mgmt.resource.resources.models import DeploymentProperties
from click import Path, argument, option
from click import command
from Babylon.utils.interactive import confirm_deploy_arm_mode
from Babylon.utils.typing import QueryType
from Babylon.utils.environment import Environment
from Babylon.utils.decorators import inject_context_with_resource
from Babylon.utils.response import CommandResponse
from Babylon.utils.clients import pass_arm_client

logger = logging.getLogger("Babylon")
env = Environment()


@command()
@pass_arm_client
@option("--complete-mode", "deploy_mode_complete", is_flag=True)
@option("--file", "deploy_file", type=Path(readable=True, dir_okay=False, path_type=pathlib.Path))
@argument("deployment_name", type=QueryType())
@inject_context_with_resource({'api': ['organization_id', 'workspace_key'], 'azure': ['resource_group_name']})
def deploy(
    context: Any,
    arm_client: ResourceManagementClient,
    deployment_name: str,
    deploy_file: Optional[Path],
    deploy_mode_complete: bool,
) -> CommandResponse:
    """
    Deploy a new function Scenario Donwload
    """
    organization_id = context['api_organization_id']
    workspace_key = context['api_workspace_key']
    resource_group_name = context['azure_resource_group_name']

    mode = DeploymentMode.INCREMENTAL
    if deploy_mode_complete:
        logger.warn("""Warning: In complete mode,\n
                    Resource Manager deletes resources that exist in the resource group but,\n
                    aren't specified in the template.""")
        if confirm_deploy_arm_mode():
            mode = DeploymentMode.COMPLETE

    deploy_file = env.working_dir.original_template_path / "arm/azf_deploy.json"
    az_app_secret = env.get_project_secret(organization_id=organization_id, workspace_key=workspace_key, name="azf")
    arm_template = env.fill_template(deploy_file,
                                     data={
                                         "instance_name": f"{organization_id.lower()}-{workspace_key.lower()}",
                                         "azure_app_client_secret": az_app_secret
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
        # check if done
        if not poller.done():
            return CommandResponse.fail()
        # deployments created

    except HttpResponseError as _e:
        logger.error(f"An error occurred : {_e.message}")
        return CommandResponse.fail()

    _ret: list[str] = ["Provisioning state: successful"]
    logger.info("\n".join(_ret))
    return CommandResponse.success()
