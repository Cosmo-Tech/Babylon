import logging
from typing import Optional

from click import argument
from click import command
from click import option

from ....utils.decorators import describe_dry_run
from ....utils.decorators import timing_decorator
from ....utils.response import CommandResponse
from ....utils.typing import QueryType
from ....utils.environment import Environment

logger = logging.getLogger("Babylon")


@command()
@argument("deployment_name", type=QueryType())
@option("-t", "--template-uri", "template_uri", type=QueryType())
@describe_dry_run("Would create a yaml file with an arm deployment config: deployment name, template link, parameters")
@timing_decorator
def create(
    deployment_name: str,
    template_uri: Optional[str] = "",
) -> CommandResponse:
    """Create a resource deployment config."""
    env = Environment()

    _azure_deployment_template = env.working_dir.get_file(".payload_templates/arm/azure_deployment.yaml")

    arm_deployment = env.fill_template(_azure_deployment_template, {
        "deployment_name": deployment_name,
        "template_uri": template_uri
    })
    with open(deployment_name + ".yaml", "w") as _f:
        _f.write(arm_deployment)

    logger.info(f"Resource deployment config created, content was dumped in {deployment_name}.yaml")
    return CommandResponse.success({"deployment_name": deployment_name})
