import json
import logging

from azure.core.exceptions import HttpResponseError
from Babylon.utils.environment import Environment
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from azure.mgmt.resource.resources.models import Deployment
from azure.mgmt.resource.resources.models import DeploymentProperties
from Babylon.utils.interactive import confirm_deploy_arm_mode
from Babylon.utils.response import CommandResponse

logger = logging.getLogger("Babylon")
env = Environment()


class AzureAppFunctionService:

    def __init__(self, arm_client: ResourceManagementClient, state: dict = None) -> None:
        self.state = state
        self.arm_client = arm_client

    def deploy(
        self,
        deployment_name: str,
        deploy_mode_complete: bool,
    ):
        organization_id = self.state["api"]["organization_id"]
        workspace_key = self.state["api"]["workspace_key"]
        workspace_key = self.state["azure"]["url_zip"]
        resource_group_name = self.state["azure"]["resource_group_name"]

        mode = DeploymentMode.INCREMENTAL
        if deploy_mode_complete:
            logger.warning("""Warning: In complete mode,\n
                        Resource Manager deletes resources that exist in the resource group but,\n
                        aren't specified in the template.""")
            if confirm_deploy_arm_mode():
                mode = DeploymentMode.COMPLETE

        deploy_file = env.original_template_path / "arm/azf_deploy.json"
        az_app_secret = env.get_project_secret(organization_id=organization_id, workspace_key=workspace_key, name="azf")
        instance_name = f"{organization_id}-{workspace_key}"
        ext_args = dict(azure_app_client_secret=az_app_secret, instance_name=instance_name)
        arm_template = env.fill_template(data=deploy_file.open().read(), state=self.state, ext_args=ext_args)
        arm_template = json.loads(arm_template)
        parameters = {k: {"value": v["defaultValue"]} for k, v in dict(arm_template["parameters"]).items()}
        logger.info("Starting deployment")

        try:
            poller = self.arm_client.deployments.begin_create_or_update(
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

    def delete(self):
        subscription_id = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        organization_id = self.state["api"]["organization_id"]
        workspace_key = self.state["api"]["workspace_key"]
        try:
            poller = self.arm_client.resources.begin_delete_by_id(
                resource_id=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}"
                f"/providers/Microsoft.Web/sites/{organization_id}-{workspace_key}",
                api_version="2019-08-01")
            poller.wait()
            # check if done
            if not poller.done():
                return False
            return True
        except HttpResponseError as _e:
            logger.error(f"An error occurred : {_e.message}")
            return False
