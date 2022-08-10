import logging
from typing import Optional

from click import argument
from click import command

from ....utils.configuration import Configuration
from ....utils.decorators import pass_config
from ....utils.interactive import select_from_list

logger = logging.getLogger("Babylon")


@command()
@pass_config
@argument("deployment", required=False, type=str)
def select_deployment(config: Configuration, deployment: Optional[str] = None):
    """Change current selected deployment

    if not argument is passed will run in interactive mode"""
    if deployment:
        if config.set_deploy(deployment):
            logger.info(f"Configuration successfully updated")
        else:
            logger.error(f"Configuration was not updated. {deployment} is not a valid deploy name.")
    else:
        logger.debug("Interactive change of deploy:")
        available_deploys = list(config.list_deploys())
        new_deploy = select_from_list(available_deploys, config.deploy)
        if new_deploy:
            config.set_deploy(new_deploy)
            logger.debug(f"Configuration successfully updated")
        else:
            logger.error("Issue while selecting new deployment configuration")
