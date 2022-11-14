import logging

from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from click import argument
from click import command
from click import make_pass_decorator
from ruamel.yaml import YAML

from ......utils.decorators import require_platform_key

logger = logging.getLogger("Babylon")

pass_arm_client = make_pass_decorator(ResourceManagementClient)


@command()
@pass_arm_client
@argument("deployment_file_path")
@require_platform_key("resource_group_name", "resource_group_name")
def deploy(
    arm_client: ResourceManagementClient,
    deployment_file_path: str,
    resource_group_name: str,
):
    """Command created from a template"""

    _commented_yaml_loader = YAML()

    with open(deployment_file_path, mode='r') as _file:
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

    try:
        poller = arm_client.deployments.begin_create_or_update(
            resource_group_name=resource_group_name,
            deployment_name=deployment_name,
            parameters=deployment_properties,
        )
    except HttpResponseError as _e:
        logger.error(f"An error occurred : {_e.message}")
        return

    adt_creation_result = poller.result()
    logger.info(adt_creation_result)
