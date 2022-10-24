import logging

import yaml
from click import command

from ....utils.configuration import Configuration
from ....utils.decorators import pass_config

logger = logging.getLogger("Babylon")


@command()
@pass_config
def validate(config: Configuration):
    """Validate current config"""
    config.check_api()
    with open(config.get_deploy_path(), "r") as file:
        for k, v in yaml.safe_load(file).items():
            if not v:
                logger.warning(f"Deployment variable `{k}` is empty")
    with open(config.get_platform_path(), "r") as file:
        for k, v in yaml.safe_load(file).items():
            if not v:
                logger.warning(f"Platform variable `{k}` is empty")
