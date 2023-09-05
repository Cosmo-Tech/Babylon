import json
import logging
import pathlib

from azure.core.exceptions import HttpResponseError
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode
from click import argument
from click import command
from click import option

from ....utils.clients import pass_arm_client
from ....utils.decorators import timing_decorator
from ....utils.environment import Environment
from ....utils.response import CommandResponse
from ....utils.typing import QueryType
from ....utils.yaml_utils import yaml_to_json

logger = logging.getLogger("Babylon")


@command()
@pass_arm_client
@argument("deployment-config-file-path", type=pathlib.Path)
@option("-r", "--resource-group-name", "resource_group_name", type=QueryType(), default="%deploy%resource_group_name")
@timing_decorator
def run(arm_client: ResourceManagementClient, deployment_config_file_path: pathlib.Path,
        resource_group_name: str) -> CommandResponse:
    """Apply a resource deployment config via arm deployment."""
    env = Environment()
    arm_deployment = env.fill_template(deployment_config_file_path)
    if deployment_config_file_path.suffix in [".yaml", ".yml"]:
        arm_deployment = yaml_to_json(arm_deployment)
    arm_deployment = json.loads(arm_deployment)
    if any(k not in arm_deployment for k in ["parameters", "template_uri", "deployment_name"]):
        logger.error("ARM deployment file is missing keys")
        return CommandResponse.fail()
    parameters = {k: {'value': v} for k, v in dict(arm_deployment["parameters"]).items()}
    deployment_properties = {
        'properties': {
            'mode': DeploymentMode.incremental,
            'template_link': {
                'uri': arm_deployment["template_uri"],
            },
            'parameters': parameters,
        }
    }

    logger.info(f"Starting {arm_deployment['deployment_name']} deployment")

    try:
        arm_client.deployments.begin_create_or_update(
            resource_group_name=resource_group_name,
            deployment_name=arm_deployment["deployment_name"],
            parameters=deployment_properties,
        )
    except HttpResponseError as _e:
        logger.error(f"An error occurred : {_e.message}")
        return CommandResponse.fail()

    logger.info("Deployment created")

    return CommandResponse.success()
