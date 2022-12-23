import logging

import yaml
from click import command

from ....utils.environment import Environment
from ....utils.response import CommandResponse

logger = logging.getLogger("Babylon")


@command()
def validate() -> CommandResponse:
    """Validate current config"""
    config = Environment().configuration
    config.check_api()
    for k, v in yaml.safe_load(open(config.get_deploy_path())).items():
        if v == "":
            logger.warning(f"Deployment variable `{k}` is empty")
    for k, v in yaml.safe_load(open(config.get_platform_path())).items():
        if v == "":
            logger.warning(f"Platform variable `{k}` is empty")
    return CommandResponse()
