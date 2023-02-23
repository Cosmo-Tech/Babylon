import logging

from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from click import argument
from click import command
from click import option

from ......utils.api import convert_keys_case
from ......utils.api import get_api_file
from ......utils.api import underscore_to_camel
from ......utils.decorators import require_deployment_key
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse
from ......utils.credentials import pass_arm_client

logger = logging.getLogger("Babylon")


@command()
@pass_arm_client
@argument("deployment-config-file-path")
@require_deployment_key("resource_group_name", "resource_group_name")
@option("-e",
        "--use-working-dir-file",
        "use_working_dir_file",
        is_flag=True,
        help="Should the ARM file path be relative to Babylon working directory ?")
@timing_decorator
def run(
    arm_client: ResourceManagementClient,
    deployment_config_file_path: str,
    resource_group_name: str,
    use_working_dir_file: bool = False,
) -> CommandResponse:
    """Apply a resource deployment config via arm deployment."""

    arm_deployment = get_api_file(api_file_path=deployment_config_file_path, use_working_dir_file=use_working_dir_file)
    formatted_parameters = convert_keys_case(arm_deployment.get("parameters"), underscore_to_camel)
    parameters = {k: {'value': v} for k, v in dict(formatted_parameters).items()}
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
        arm_client.deployments.begin_create_or_update(
            resource_group_name=resource_group_name,
            deployment_name=deployment_name,
            parameters=deployment_properties,
        )
    except HttpResponseError as _e:
        logger.error(f"An error occurred : {_e.message}")
        return CommandResponse.fail()

    logger.info("Deployment created")

    return CommandResponse.success()
