import pathlib

from logging import getLogger
from Babylon.utils.environment import Environment
from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import Deployment
from azure.mgmt.resource.resources.models import DeploymentMode
from azure.mgmt.resource.resources.models import DeploymentProperties

from Babylon.utils.interactive import confirm_deploy_arm_mode
from Babylon.utils.response import CommandResponse

logger = getLogger("Babylon")
env = Environment()


class ArmService:

    def __init__(self, state: dict, arm_client: ResourceManagementClient) -> None:
        self.state = state
        self.arm_client = arm_client

    def run(
        self,
        deployment_name: str,
        file: str,
        ext_args: dict = None,
        deploy_mode_complete: bool = False,
    ):
        resource_group_name = self.state["azure"]["resource_group_name"]
        deploy_file = pathlib.Path(env.convert_template_path(f"%templates%/arm/{file}"))
        mode = DeploymentMode.INCREMENTAL
        if deploy_mode_complete:
            logger.warning("""Warning: In complete mode\n
                        Resource Manager deletes resources that exist in the resource group,\n
                        but aren't specified in the template.""")
            if confirm_deploy_arm_mode():
                mode = DeploymentMode.COMPLETE

        if not deploy_file:
            logger.error("[arm] deploy file not found")
            return CommandResponse.fail()
        arm_template = env.fill_template(
            data=deploy_file.open().read(),
            state=dict(services=self.state),
            ext_args=ext_args,
        )
        parameters = {k: {"value": v["defaultValue"]} for k, v in dict(arm_template["parameters"]).items()}
        try:
            poller = self.arm_client.deployments.begin_create_or_update(
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
        logger.info(f"[arm] provisioning state {file}: successful")
        return CommandResponse.success()

    def delete_event_hub(self):
        subscription_id = self.state["azure"]["subscription_id"]
        resource_group_name = self.state["azure"]["resource_group_name"]
        organization_id = self.state["api"]["organization_id"]
        workspace_key = self.state["api"]["workspace_key"]
        try:
            poller = self.arm_client.resources.begin_delete_by_id(
                resource_id=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}"
                f"/providers/Microsoft.EventHub/namespaces/{organization_id}-{workspace_key}",
                api_version="2017-04-01",
            )
            poller.wait()
            # check if done
            if not poller.done():
                return False
            return True
        except HttpResponseError as _e:
            logger.error(f"[arm] an error occurred : {_e.message}")
            return False
