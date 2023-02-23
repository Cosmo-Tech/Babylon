import logging
from typing import Optional

from click import argument
from click import command
from click import option
from ruamel.yaml import YAML

from ......utils import TEMPLATE_FOLDER_PATH
from ......utils.decorators import describe_dry_run
from ......utils.decorators import timing_decorator
from ......utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
@argument("deployment_name")
@option("-t", "--template-uri", "template_uri")
@describe_dry_run("Would create a yaml file with an arm deployment config: deployment name, template link, parameters")
@timing_decorator
def create(
    deployment_name: str,
    template_uri: Optional[str] = "",
) -> CommandResponse:
    """Create a resource deployment config."""

    _azure_deployment_template = TEMPLATE_FOLDER_PATH / "azure_resource_manager/azure_deployment.yaml"
    _commented_yaml_loader = YAML()

    with open(_azure_deployment_template, mode='r') as file:
        arm_deployment = _commented_yaml_loader.load(file)

    arm_deployment["deployment_name"] = deployment_name
    arm_deployment["template_uri"] = template_uri

    with open(deployment_name + ".yaml", "w") as _f:
        _commented_yaml_loader.dump(arm_deployment, _f)

    logger.info(f"Resource deployment config created, content was dumped in {deployment_name}.yaml")
    return CommandResponse.success({"deployment_name": deployment_name})
