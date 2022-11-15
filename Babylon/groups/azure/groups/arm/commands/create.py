import logging
from typing import Optional

from azure.mgmt.resource import ResourceManagementClient
from click import argument
from click import command
from click import make_pass_decorator
from click import option
from ruamel.yaml import YAML

from ......utils import TEMPLATE_FOLDER_PATH

logger = logging.getLogger("Babylon")

pass_arm_client = make_pass_decorator(ResourceManagementClient)


@command()
@pass_arm_client
@argument("deployment_name")
@option("-t", "--template-uri", "template_uri")
def create(
    deployment_name: str,
    template_uri: Optional[str] = '',
):
    """Command created from a template"""

    _azure_deployment_template = TEMPLATE_FOLDER_PATH / "azure_ressouce_manager/azure_deployment.yaml"
    _commented_yaml_loader = YAML()

    with open(_azure_deployment_template, mode='r') as file:
        arm_deployment = _commented_yaml_loader.load(file)

    arm_deployment["deployment_name"] = deployment_name
    arm_deployment["template_uri"] = template_uri

    with open(deployment_name + ".yaml", "w") as _f:
        _commented_yaml_loader.dump(arm_deployment, _f)
