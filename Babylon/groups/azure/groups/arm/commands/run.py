import logging
from typing import Optional

from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from click import argument
from click import command
from click import make_pass_decorator
from ruamel.yaml import YAML

from ......utils.decorators import require_platform_key
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")

pass_arm_client = make_pass_decorator(ResourceManagementClient)


@command()
@pass_arm_client
@argument("deployment-config-file-path")
@require_platform_key("resource_group_name", "resource_group_name")
def run(
    arm_client: ResourceManagementClient,
    deployment_config_file_path: str,
    resource_group_name: str,
) -> CommandResponse:
    """Apply a resource deployment config via arm deployment."""

    _commented_yaml_loader = YAML()

    with open(deployment_config_file_path, mode='r') as _file:
        arm_deployment = _commented_yaml_loader.load(_file)

    parameters = {k: {'value': v} for k, v in arm_deployment.get("parameters").items()}
    template_uri = arm_deployment.get("template_uri")
    deployment_name = arm_deployment.get("deployment_name")
    deployment_properties = dict({
        'properties': {
            'mode': DeploymentMode.incremental,
            'template_link': {
                'uri': template_uri,
            },
            'parameters': parameters,
        }
    })

    logger.info(f"Starting {deployment_name} deployment")

    try:
        poller = arm_client.deployments.begin_create_or_update(
            resource_group_name=resource_group_name,
            deployment_name=deployment_name,
            parameters=deployment_properties,
        )
    except HttpResponseError as _e:
        logger.error(f"An error occurred : {_e.message}")
        return

    logger.debug(poller.result())
    logger.info(f"Deployment finished with status : {poller.status()}. \
                 \nMore details at : {poller.result()['id']}")

    return CommandResponse(data={"status": poller.status()})
